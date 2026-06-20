# -*- coding: utf-8 -*-
"""
Brevia · cápsulas de contexto (B2)

El ahorro ESTRUCTURAL grande: en vez de re-pegar el mismo documento/instrucciones
en cada turno, lo guardas UNA vez como cápsula y solo mandas una referencia corta.

  pack:   reemplaza el contenido de una cápsula por  [[cap:NOMBRE]]   (ahorro real)
  expand: reemplaza  [[cap:NOMBRE]]  por el contenido completo

Trabaja a nivel de bloque (párrafo), igual que el dedup del motor. El que consume
las referencias (Claude vía MCP, o el proxy) llama a `expand` cuando necesita el
contenido — así no se reenvía el documento entero cada vez.

Almacén por defecto: ~/.brevia/capsules.json  (persistente entre sesiones).
Sin dependencias externas.
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_STORE = Path.home() / ".brevia" / "capsules.json"
MARKER_RE = re.compile(r"\[\[cap:([A-Za-z0-9_\-]+)\]\]")


def _norm(text):
    """Clave normalizada para comparar bloques (ignora espacios/mayúsculas)."""
    return re.sub(r"\s+", " ", text).strip().lower()


def _est_tokens(text):
    chars = len(text)
    words = len(re.findall(r"\S+", text))
    return int(round((chars / 4 + words / 0.75) / 2))


class CapsuleStore:
    def __init__(self, path=DEFAULT_STORE):
        self.path = Path(path)
        self.data = {"capsules": {}}
        if self.path.is_file():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.data = {"capsules": {}}
        self.data.setdefault("capsules", {})

    def _flush(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    # --- CRUD --- #
    def save(self, name, text):
        text = text.strip()
        self.data["capsules"][name] = {
            "text": text,
            "key": _norm(text),
            "tokens": _est_tokens(text),
            "chars": len(text),
        }
        self._flush()
        return {"name": name, "tokens": self.data["capsules"][name]["tokens"],
                "chars": len(text)}

    def get(self, name):
        c = self.data["capsules"].get(name)
        return c["text"] if c else None

    def delete(self, name):
        return self.data["capsules"].pop(name, None) is not None and (self._flush() or True)

    def list(self):
        return [{"name": n, "tokens": c["tokens"], "chars": c["chars"]}
                for n, c in self.data["capsules"].items()]

    # --- operaciones de ahorro --- #
    def pack(self, text):
        """Reemplaza bloques que coinciden con cápsulas por su referencia."""
        keymap = {c["key"]: n for n, c in self.data["capsules"].items()}
        blocks = re.split(r"(\n\s*\n)", text)  # conserva separadores
        out = []
        replaced = []
        for b in blocks:
            if b.strip() and _norm(b) in keymap:
                name = keymap[_norm(b)]
                out.append(f"[[cap:{name}]]")
                replaced.append(name)
            else:
                out.append(b)
        packed = "".join(out)
        t_in, t_out = _est_tokens(text), _est_tokens(packed)
        return {"text": packed, "replaced": replaced,
                "tokens_in": t_in, "tokens_out": t_out, "saved": t_in - t_out}

    def expand(self, text):
        """Reemplaza referencias ⟦cap:NOMBRE⟧ por el contenido completo."""
        missing = []

        def sub(m):
            name = m.group(1)
            c = self.data["capsules"].get(name)
            if not c:
                missing.append(name)
                return m.group(0)
            return c["text"]

        return {"text": MARKER_RE.sub(sub, text), "missing": missing}

    def suggest(self, text, min_tokens=40):
        """Sugiere bloques grandes (aún no encapsulados) que convendría guardar."""
        existing = {c["key"] for c in self.data["capsules"].values()}
        blocks = [b for b in re.split(r"\n\s*\n", text) if b.strip()]
        seen = {}
        for b in blocks:
            k = _norm(b)
            seen.setdefault(k, {"count": 0, "tokens": _est_tokens(b), "sample": b[:80]})
            seen[k]["count"] += 1
        sugg = []
        for k, info in seen.items():
            if k in existing:
                continue
            # vale la pena si es grande, o si se repite
            if info["tokens"] >= min_tokens or info["count"] > 1:
                sugg.append({"tokens": info["tokens"], "repeats": info["count"],
                             "sample": info["sample"]})
        sugg.sort(key=lambda s: (-s["repeats"], -s["tokens"]))
        return sugg


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _read_input(args):
    if args.file:
        return Path(args.file).read_text(encoding="utf-8", errors="replace")
    if args.text:
        return args.text
    return sys.stdin.read()


def main():
    ap = argparse.ArgumentParser(description="Brevia — cápsulas de contexto")
    ap.add_argument("--store", default=str(DEFAULT_STORE), help="ruta del almacén")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("save", help="guardar una cápsula")
    p.add_argument("name")
    p.add_argument("--file"); p.add_argument("--text")

    sub.add_parser("list", help="listar cápsulas")

    p = sub.add_parser("get", help="ver el contenido de una cápsula"); p.add_argument("name")
    p = sub.add_parser("delete", help="borrar una cápsula"); p.add_argument("name")

    for name in ("pack", "expand", "suggest"):
        p = sub.add_parser(name)
        p.add_argument("--file"); p.add_argument("--text")

    args = ap.parse_args()
    store = CapsuleStore(args.store)

    def w(s):
        sys.stdout.buffer.write((s + "\n").encode("utf-8", errors="replace"))

    if args.cmd == "save":
        info = store.save(args.name, _read_input(args))
        w(f"cápsula '{info['name']}' guardada · {info['tokens']} tokens · {info['chars']} chars")
    elif args.cmd == "list":
        items = store.list()
        if not items:
            w("(sin cápsulas)")
        for it in items:
            w(f"  {it['name']:<20} {it['tokens']:>6} tokens  ({it['chars']} chars)")
    elif args.cmd == "get":
        t = store.get(args.name)
        w(t if t is not None else f"(no existe '{args.name}')")
    elif args.cmd == "delete":
        w("borrada" if store.delete(args.name) else "no existía")
    elif args.cmd == "pack":
        r = store.pack(_read_input(args))
        w(f"pack: {r['tokens_in']} -> {r['tokens_out']} tokens (-{r['saved']})  "
          f"reemplazadas: {', '.join(r['replaced']) or 'ninguna'}")
        w("--- texto ---"); w(r["text"])
    elif args.cmd == "expand":
        r = store.expand(_read_input(args))
        if r["missing"]:
            w(f"(faltan cápsulas: {', '.join(r['missing'])})")
        w(r["text"])
    elif args.cmd == "suggest":
        sugg = store.suggest(_read_input(args))
        if not sugg:
            w("(nada que sugerir)")
        for s in sugg:
            w(f"  ~{s['tokens']} tokens · x{s['repeats']} · \"{s['sample']}...\"")


if __name__ == "__main__":
    main()
