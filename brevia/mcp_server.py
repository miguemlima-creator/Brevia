# -*- coding: utf-8 -*-
"""
Brevia · servidor MCP (B5) — stdlib pura, sin dependencias.

Expone Brevia DENTRO de Claude (Code o Desktop) como herramientas MCP:
  brevia_compress   — comprime texto (dedup + opcional recorte), devuelve texto + ahorro
  brevia_savings    — solo mide el ahorro (no devuelve el texto)
  capsule_save      — guarda un bloque reutilizable
  capsule_list      — lista cápsulas
  capsule_pack      — reemplaza contenido conocido por referencias [[cap:NOMBRE]]
  capsule_expand    — expande referencias a su contenido
  capsule_suggest   — sugiere qué bloques convendría encapsular

Protocolo: JSON-RPC 2.0 sobre stdio, mensajes delimitados por línea (MCP stdio).
IMPORTANTE: stdout solo lleva mensajes JSON-RPC. Los logs van a stderr.

Registrar en Claude Code (.mcp.json o config):
  { "mcpServers": { "brevia": { "command": "python",
      "args": ["<ruta>/brevia/mcp_server.py"] } } }
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compress  # noqa: E402
from capsules import CapsuleStore  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "brevia", "version": "0.1.0"}

_counter, _method = compress._tiktoken_counter()
_method = _method or "estimacion char/4"
_store = CapsuleStore()


def log(*a):
    print("[brevia-mcp]", *a, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- #
# Implementación de cada herramienta → devuelve string para el bloque de texto
# --------------------------------------------------------------------------- #
def t_compress(args):
    text = args.get("text", "")
    aggr = bool(args.get("aggressive", False))
    out, t_in, t_out, trace = compress.compress(text, aggressive=aggr, counter=_counter)
    saved = t_in - t_out
    pct = round(saved / t_in * 100, 1) if t_in else 0
    header = f"[Brevia] {t_in} -> {t_out} tokens (-{saved} | {pct}% menos) · método {_method}\n\n"
    return header + out


def t_savings(args):
    text = args.get("text", "")
    aggr = bool(args.get("aggressive", False))
    _, t_in, t_out, trace = compress.compress(text, aggressive=aggr, counter=_counter)
    saved = t_in - t_out
    pct = round(saved / t_in * 100, 1) if t_in else 0
    steps = {s["paso"]: s["ahorro"] for s in trace if s["ahorro"]}
    return json.dumps({"tokens_in": t_in, "tokens_out": t_out, "saved": saved,
                       "pct": pct, "by_step": steps, "method": _method},
                      ensure_ascii=False)


def t_capsule_save(args):
    info = _store.save(args["name"], args.get("text", ""))
    return f"cápsula '{info['name']}' guardada · {info['tokens']} tokens"


def t_capsule_list(args):
    items = _store.list()
    if not items:
        return "(sin cápsulas)"
    return "\n".join(f"{it['name']}: {it['tokens']} tokens" for it in items)


def t_capsule_pack(args):
    r = _store.pack(args.get("text", ""))
    header = (f"[pack] {r['tokens_in']} -> {r['tokens_out']} tokens (-{r['saved']}) · "
              f"reemplazadas: {', '.join(r['replaced']) or 'ninguna'}\n\n")
    return header + r["text"]


def t_capsule_expand(args):
    r = _store.expand(args.get("text", ""))
    note = f"(faltan cápsulas: {', '.join(r['missing'])})\n\n" if r["missing"] else ""
    return note + r["text"]


def t_capsule_suggest(args):
    sugg = _store.suggest(args.get("text", ""))
    if not sugg:
        return "(nada que sugerir)"
    return "\n".join(f"~{s['tokens']} tokens x{s['repeats']}: {s['sample']}..." for s in sugg)


TOOLS = [
    {
        "name": "brevia_compress",
        "description": "Comprime texto antes de enviarlo a un LLM (dedup sin pérdida + recorte opcional de relleno). Devuelve el texto comprimido y cuántos tokens ahorró. No toca código.",
        "handler": t_compress,
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto a comprimir"},
                "aggressive": {"type": "boolean", "description": "También quita relleno/cortesía (default false)"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "brevia_savings",
        "description": "Mide cuántos tokens ahorraría comprimir un texto, sin devolver el texto. Útil para reportar el ahorro.",
        "handler": t_savings,
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "aggressive": {"type": "boolean"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "capsule_save",
        "description": "Guarda un bloque reutilizable (documento, instrucciones) como cápsula con un nombre, para no re-pegarlo en cada turno.",
        "handler": t_capsule_save,
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nombre corto de la cápsula"},
                "text": {"type": "string", "description": "Contenido a guardar"},
            },
            "required": ["name", "text"],
        },
    },
    {
        "name": "capsule_list",
        "description": "Lista las cápsulas guardadas con su tamaño en tokens.",
        "handler": t_capsule_list,
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "capsule_pack",
        "description": "Reemplaza en el texto cualquier contenido que coincida con una cápsula por una referencia corta [[cap:NOMBRE]]. Ahorro estructural grande.",
        "handler": t_capsule_pack,
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
    {
        "name": "capsule_expand",
        "description": "Expande las referencias [[cap:NOMBRE]] de un texto a su contenido completo.",
        "handler": t_capsule_expand,
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
    {
        "name": "capsule_suggest",
        "description": "Sugiere qué bloques grandes o repetidos de un texto convendría guardar como cápsula.",
        "handler": t_capsule_suggest,
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
]
TOOL_BY_NAME = {t["name"]: t for t in TOOLS}


# --------------------------------------------------------------------------- #
# Bucle JSON-RPC
# --------------------------------------------------------------------------- #
def make_result(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def make_error(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle(msg):
    method = msg.get("method")
    req_id = msg.get("id")

    if method == "initialize":
        return make_result(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })
    if method == "notifications/initialized":
        return None  # notificación, sin respuesta
    if method == "ping":
        return make_result(req_id, {})
    if method == "tools/list":
        return make_result(req_id, {
            "tools": [{"name": t["name"], "description": t["description"],
                       "inputSchema": t["inputSchema"]} for t in TOOLS]
        })
    if method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {}) or {}
        tool = TOOL_BY_NAME.get(name)
        if not tool:
            return make_error(req_id, -32602, f"herramienta desconocida: {name}")
        try:
            text = tool["handler"](args)
            return make_result(req_id, {"content": [{"type": "text", "text": text}]})
        except Exception as e:
            return make_result(req_id, {
                "content": [{"type": "text", "text": f"error: {e}"}], "isError": True})

    if req_id is not None:
        return make_error(req_id, -32601, f"método no soportado: {method}")
    return None  # notificación desconocida


def main():
    # MCP exige UTF-8; en Windows stdin/stdout caen a cp1252 por defecto.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    log(f"iniciado · {len(TOOLS)} tools · tokens={_method}")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
