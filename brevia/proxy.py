# -*- coding: utf-8 -*-
"""
Brevia · proxy / gateway (B6, scaffold)

El ahorro de tokens REAL "dentro de la ingeniería", model-agnostic.

  App / Agente  ──>  [ BREVIA PROXY ]  ──>  OpenAI / Anthropic / Google
                     comprime aquí       (forward con tu API key)

La app apunta su base_url al proxy (ej. http://localhost:8800/v1). El proxy:
  1. recibe el request estilo OpenAI (/v1/chat/completions)
  2. comprime el `content` de cada mensaje (dedup sin pérdida + recorte opcional)
  3. mide el ahorro y lo acumula en un medidor vivo (/stats)
  4. reenvía al proveedor real con tu Authorization  (o responde en --dry-run)

Sin dependencias externas (http.server + urllib). Scaffold: funcional y honesto,
listo para crecer (cápsulas, semántico, multi-proveedor).

Uso:
  python proxy.py --dry-run                 # prueba sin reenviar (devuelve el ahorro)
  python proxy.py --upstream https://api.openai.com --aggressive
"""
import argparse
import hashlib
import json
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compress  # noqa: E402
import semantic  # noqa: E402
from capsules import CapsuleStore  # noqa: E402

_counter, _method = compress._tiktoken_counter()
_method = _method or "estimacion char/4"
_store = CapsuleStore()

# medidor acumulado (token meter vivo)
METER = {"requests": 0, "tokens_in": 0, "tokens_out": 0, "saved": 0,
         "dup_msgs_removed": 0, "cache_hits": 0}

CFG = {"upstream": "https://api.openai.com", "aggressive": False, "dry_run": False,
       "semantic": False, "keep": 0.7, "capsules": False, "cache": False}

# caché de respuestas exactas (hash del payload comprimido -> body)
RESP_CACHE = {}


def _norm(s):
    import re
    return re.sub(r"\s+", " ", s).strip().lower()


def dedup_messages(messages):
    """Quita mensajes EXACTAMENTE duplicados (mismo role+content), conserva el 1ro.
    Seguro: algunos agentes reenvían el mismo mensaje por bug."""
    seen = set()
    out = []
    removed = 0
    for m in messages:
        c = m.get("content")
        key = (m.get("role"), _norm(c)) if isinstance(c, str) else id(m)
        if isinstance(c, str) and key in seen:
            removed += 1
            continue
        if isinstance(c, str):
            seen.add(key)
        out.append(m)
    return out, removed


def compress_messages(messages):
    """Procesa los mensajes: (opcional) expande cápsulas, dedup de mensajes, y
    comprime el content de cada uno (regex o semántico). Devuelve (nuevos, t_in, t_out, removed).
    t_in cuenta TODOS los mensajes originales (incluye los duplicados eliminados) para
    acreditar honestamente el ahorro del dedup."""
    t_in = sum(compress.count_tokens(m["content"], _counter)
               for m in messages if isinstance(m.get("content"), str))
    messages, removed = dedup_messages(messages)
    t_out = 0
    out = []
    for m in messages:
        content = m.get("content")
        if not isinstance(content, str):
            out.append(m)  # multimodal / no-string: intacto
            continue
        if CFG["capsules"]:
            content = _store.expand(content)["text"]
        if CFG["semantic"]:
            r = semantic.compress_semantic(content, keep=CFG["keep"])
            comp, to = r["text"], r["tokens_out"]
        else:
            comp, _ti, to, _ = compress.compress(
                content, aggressive=CFG["aggressive"], counter=_counter)
        t_out += to
        nm = dict(m)
        nm["content"] = comp
        out.append(nm)
    return out, t_in, t_out, removed


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silenciar el log por defecto
        pass

    def _send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/") == "/stats":
            pct = round(METER["saved"] / METER["tokens_in"] * 100, 1) if METER["tokens_in"] else 0
            self._send_json(200, {**METER, "pct": pct, "method": _method})
        else:
            self._send_json(404, {"error": "usa POST /v1/chat/completions o GET /stats"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send_json(400, {"error": "JSON inválido"})
            return

        messages = payload.get("messages", [])
        new_msgs, t_in, t_out, removed = compress_messages(messages)
        saved = t_in - t_out
        payload["messages"] = new_msgs

        # actualizar medidor
        METER["requests"] += 1
        METER["tokens_in"] += t_in
        METER["tokens_out"] += t_out
        METER["saved"] += saved
        METER["dup_msgs_removed"] += removed
        pct = round(saved / t_in * 100, 1) if t_in else 0
        extra = f" · {removed} msg dup quitados" if removed else ""
        print(f"[brevia-proxy] req#{METER['requests']}  {t_in}->{t_out} tokens "
              f"(-{saved} | {pct}%){extra}  acumulado -{METER['saved']}", file=sys.stderr, flush=True)

        # caché de respuestas exactas (ahorra la llamada entera si se repite)
        cache_key = None
        if CFG["cache"]:
            cache_key = hashlib.sha256(
                json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest()
            if cache_key in RESP_CACHE:
                METER["cache_hits"] += 1
                body = RESP_CACHE[cache_key]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("X-Brevia-Cache", "HIT")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

        if CFG["dry_run"]:
            self._send_json(200, {
                "brevia": {"tokens_in": t_in, "tokens_out": t_out, "saved": saved,
                           "pct": pct, "dup_msgs_removed": removed,
                           "semantic": CFG["semantic"], "method": _method},
                "note": "dry-run: NO se reenvió al proveedor. El payload comprimido está listo.",
                "compressed_messages": new_msgs,
            })
            return

        # reenviar al proveedor real
        url = CFG["upstream"].rstrip("/") + self.path
        fwd_headers = {}
        for h in ("Authorization", "Content-Type", "OpenAI-Organization",
                  "anthropic-version", "x-api-key"):
            if h in self.headers:
                fwd_headers[h] = self.headers[h]
        fwd_headers.setdefault("Content-Type", "application/json")
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=fwd_headers, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read()
                if cache_key is not None and resp.status == 200:
                    RESP_CACHE[cache_key] = body
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.send_header("X-Brevia-Saved-Tokens", str(saved))
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self._send_json(502, {"error": f"fallo al reenviar: {e}"})


def main():
    ap = argparse.ArgumentParser(description="Brevia proxy / gateway")
    ap.add_argument("--port", type=int, default=8800)
    ap.add_argument("--upstream", default=CFG["upstream"],
                    help="base URL del proveedor (default OpenAI)")
    ap.add_argument("--aggressive", action="store_true", help="además quita relleno")
    ap.add_argument("--semantic", action="store_true",
                    help="compresión semántica LOSSY (resume) en vez de solo dedup")
    ap.add_argument("--keep", type=float, default=0.7,
                    help="con --semantic: fracción a conservar (default 0.7)")
    ap.add_argument("--capsules", action="store_true",
                    help="expande referencias [[cap:NOMBRE]] antes de reenviar")
    ap.add_argument("--cache", action="store_true",
                    help="caché de respuestas exactas (ahorra llamadas repetidas)")
    ap.add_argument("--dry-run", action="store_true",
                    help="no reenvía: devuelve el ahorro y el payload comprimido")
    args = ap.parse_args()
    CFG["upstream"] = args.upstream
    CFG["aggressive"] = args.aggressive
    CFG["semantic"] = args.semantic
    CFG["keep"] = args.keep
    CFG["capsules"] = args.capsules
    CFG["cache"] = args.cache
    CFG["dry_run"] = args.dry_run

    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    mode = "DRY-RUN" if args.dry_run else f"-> {args.upstream}"
    print(f"[brevia-proxy] escuchando en http://127.0.0.1:{args.port}  {mode}  "
          f"(aggressive={args.aggressive}, tokens={_method})", file=sys.stderr, flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[brevia-proxy] detenido.", file=sys.stderr)


if __name__ == "__main__":
    main()
