# -*- coding: utf-8 -*-
"""
Brevia · compresor de prompts model-agnostic (MVP v0.1)

Idea: comprimir el texto ANTES de que llegue al modelo.
  - Sirve a CUALQUIER LLM (Claude, GPT, Gemini...) porque es pre-procesamiento.
  - Sirve a CUALQUIER usuario: no solo developers, tambien quien solo usa el chat.
  - Doble ahorro: menos tokens facturados  +  menos bytes viajando (ancho de banda/energia).

Filosofia: por defecto SOLO compresion sin perdida de significado (whitespace + dedup).
La compresion "agresiva" (quitar relleno/cortesia) es opt-in y conservadora.
Nunca cambiamos el significado a tus espaldas.

Sin dependencias obligatorias. Usa tiktoken si esta instalado (mas exacto);
si no, cae a un estimador de tokens calibrado. Corre 100% offline.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Conteo de tokens
# --------------------------------------------------------------------------- #
def _tiktoken_counter():
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return lambda s: len(enc.encode(s)), "tiktoken/cl100k_base"
    except Exception:
        return None, None


def count_tokens(text, counter=None):
    """Cuenta tokens. Con tiktoken es exacto (GPT) y buen proxy para Claude.
    Sin tiktoken usa heuristica char/4 — estimacion, no factura real."""
    if counter:
        return counter(text)
    # Heuristica: ~4 chars/token en ingles, algo mas en espanol/codigo.
    # Promediamos char/4 con palabras/0.75 para no sub-estimar.
    chars = len(text)
    words = len(re.findall(r"\S+", text))
    return int(round((chars / 4 + words / 0.75) / 2))


# --------------------------------------------------------------------------- #
# Pasos de compresion — cada uno: text -> text
# Los SEGUROS no cambian el significado. Los AGRESIVOS son opt-in.
# --------------------------------------------------------------------------- #
def normalize_whitespace(text):
    """Colapsa espacios repetidos y lineas en blanco de sobra. Sin perdida."""
    # espacios/tabs multiples -> uno
    text = re.sub(r"[ \t]+", " ", text)
    # espacios al final de cada linea
    text = re.sub(r"[ \t]+\n", "\n", text)
    # 3+ saltos de linea -> 2 (mantiene separacion de parrafos)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def dedup_blocks(text):
    """Quita parrafos duplicados exactos (caso clasico: pegar el mismo
    contexto/documento dos veces). Sin perdida — el modelo no necesita el
    duplicado. Conserva el ORDEN de la primera aparicion."""
    blocks = re.split(r"\n\s*\n", text)
    seen = set()
    out = []
    for b in blocks:
        key = re.sub(r"\s+", " ", b).strip().lower()
        if len(key) < 12:          # no deduplicar lineas muy cortas
            out.append(b)
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(b)
    return "\n\n".join(out)


def trim_lines(text):
    """Recorta espacios al inicio/fin de cada linea. Sin perdida."""
    return "\n".join(line.strip() for line in text.split("\n"))


# --- AGRESIVOS (opt-in con --aggressive) --- #
# Frases de relleno/cortesia que no cambian la TAREA. Bilingue ES/EN.
FILLER_PATTERNS = [
    r"\bme gustar[ií]a que (?:por favor )?",
    r"\bquisiera (?:pedirte |saber )?(?:si )?",
    r"\bte agradecer[ií]a (?:mucho )?(?:si )?",
    r"\bsi (?:no es mucha molestia|pudieras|fueras tan amable)\b,?",
    r"\bpor favor\b,?",
    r"\bla verdad es que\b,?",
    r"\bcomo te (?:dec[ií]a|comentaba)\b,?",
    r"\bla neta\b,?",
    r"\bmuchas gracias(?: de antemano)?\b\.?",
    r"\bgracias de antemano\b\.?",
    r"\bI was wondering if you could\b",
    r"\bcould you (?:please )?",
    r"\bwould you (?:kindly|please )?",
    r"\bI would (?:really )?(?:like|appreciate it) (?:if )?",
    r"\bplease\b,?",
    r"\bthank you(?: (?:so much|in advance))?\b\.?",
    r"\bjust (?:wanted|wondering)\b",
    r"\bas an AI(?: language model)?\b,?",
    r"\bif that(?:'s| is) (?:ok|okay|alright)\b,?",
]
FILLER_RE = re.compile("|".join(FILLER_PATTERNS), re.IGNORECASE)


def strip_filler(text):
    """Quita cortesia/relleno que no cambia la instruccion. OPT-IN.
    Conservador: no toca contenido entre comillas ni bloques de codigo."""
    # protege bloques de codigo ```...``` y `inline`
    vault = []

    def stash(m):
        vault.append(m.group(0))
        return f"\x00{len(vault)-1}\x00"

    protected = re.sub(r"```.*?```|`[^`]+`", stash, text, flags=re.DOTALL)
    protected = FILLER_RE.sub("", protected)
    protected = re.sub(r"[ \t]{2,}", " ", protected)
    protected = re.sub(r"\s+([,.;:!?])", r"\1", protected)   # espacio antes de puntuacion

    def restore(m):
        return vault[int(m.group(1))]

    return re.sub(r"\x00(\d+)\x00", restore, protected)


def collapse_markdown_noise(text):
    """Reduce decoracion que cuesta tokens y aporta poco al modelo:
    lineas de '---' repetidas, emojis decorativos en cadena. OPT-IN."""
    text = re.sub(r"\n-{3,}\n", "\n", text)
    # cadenas de 3+ emojis/simbolos decorativos -> uno
    text = re.sub(r"([\U0001F300-\U0001FAFF☀-➿]{1})[\U0001F300-\U0001FAFF☀-➿\s]{2,}", r"\1 ", text)
    return text


SAFE_STEPS = [
    ("dedup_parrafos", dedup_blocks),
    ("normalizar_espacios", normalize_whitespace),
    ("recortar_lineas", trim_lines),
]
AGGRESSIVE_STEPS = [
    ("quitar_relleno", strip_filler),
    ("reducir_decoracion", collapse_markdown_noise),
]


# --------------------------------------------------------------------------- #
# Pipeline + reporte
# --------------------------------------------------------------------------- #
CODE_VAULT_RE = re.compile(r"```.*?```|`[^`]+`", re.DOTALL)


def vault_code(text):
    """Saca los bloques de codigo del texto y los reemplaza por marcadores
    SIN espacios, para que ningun paso de compresion toque su indentacion.
    Devuelve (texto_sin_codigo, lista_de_bloques)."""
    vault = []

    def stash(m):
        vault.append(m.group(0))
        return f"\x00\x00CODE{len(vault)-1}\x00\x00"

    return CODE_VAULT_RE.sub(stash, text), vault


def restore_code(text, vault):
    return re.sub(r"\x00\x00CODE(\d+)\x00\x00",
                  lambda m: vault[int(m.group(1))], text)


def compress(text, aggressive=False, counter=None):
    steps = list(SAFE_STEPS)
    if aggressive:
        steps += AGGRESSIVE_STEPS

    before_total = count_tokens(text, counter)
    # blindar el codigo ANTES de cualquier paso (protege indentacion)
    current, vault = vault_code(text)
    trace = []
    for name, fn in steps:
        before = count_tokens(current, counter)
        current = fn(current)
        after = count_tokens(current, counter)
        trace.append({"paso": name, "tokens_antes": before, "tokens_despues": after,
                      "ahorro": before - after})
    # re-normaliza al final por si un paso (ej. quitar_relleno) dejo espacios sueltos
    current = trim_lines(normalize_whitespace(current))
    current = normalize_whitespace(current)
    # devolver el codigo intacto
    current = restore_code(current, vault)
    after_total = count_tokens(current, counter)
    return current, before_total, after_total, trace


def report(text_in, text_out, t_in, t_out, trace, method,
           price_in=3.0, sends=1000):
    """price_in = USD por 1M tokens de entrada (default aprox; verifica el
    pricing real de tu modelo). sends = cuantas veces mandarias este prompt."""
    saved = t_in - t_out
    pct = (saved / t_in * 100) if t_in else 0
    bytes_in = len(text_in.encode("utf-8"))
    bytes_out = len(text_out.encode("utf-8"))
    bytes_saved = bytes_in - bytes_out
    usd_per_send = saved / 1_000_000 * price_in
    usd_batch = usd_per_send * sends

    def w(s):
        sys.stdout.buffer.write((s + "\n").encode("utf-8", errors="replace"))

    w("")
    w("  BREVIA · reporte de compresion")
    w("  " + "-" * 42)
    w(f"  tokens   : {t_in:>7,}  ->  {t_out:>7,}   ({saved:+,} | {pct:.1f}% menos)")
    w(f"  bytes    : {bytes_in:>7,}  ->  {bytes_out:>7,}   ({bytes_saved:+,} B menos)")
    w(f"  metodo   : {method}")
    w("")
    w(f"  por envio        : ${usd_per_send:.6f}  (a ${price_in}/1M tokens in)")
    w(f"  x {sends:,} envios  : ${usd_batch:.4f}")
    w("")
    if trace:
        w("  desglose por paso:")
        for s in trace:
            if s["ahorro"]:
                w(f"    {s['paso']:<22} {s['ahorro']:+,} tokens")
    w("")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description="Brevia — comprime un prompt antes de mandarlo al LLM (ahorra tokens + datos).")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--file", help="archivo de entrada")
    src.add_argument("--text", help="texto directo")
    ap.add_argument("-a", "--aggressive", action="store_true",
                    help="ademas quita relleno/cortesia (opt-in, conservador)")
    ap.add_argument("--price-in", type=float, default=3.0,
                    help="USD por 1M tokens de entrada (default 3.0, verifica el real)")
    ap.add_argument("--sends", type=int, default=1000,
                    help="cuantos envios para estimar ahorro acumulado")
    ap.add_argument("--out", help="guardar texto comprimido en archivo")
    ap.add_argument("--json", action="store_true", help="salida JSON (para integrar)")
    ap.add_argument("--diff", action="store_true", help="mostrar el texto comprimido")
    args = ap.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="replace")
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    counter, method = _tiktoken_counter()
    method = method or "heuristica char/4 (estimacion, instala tiktoken para exactitud)"

    out, t_in, t_out, trace = compress(text, aggressive=args.aggressive, counter=counter)

    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")

    if args.json:
        saved = t_in - t_out
        result = {
            "tokens_in": t_in, "tokens_out": t_out, "saved": saved,
            "pct": round(saved / t_in * 100, 2) if t_in else 0,
            "bytes_in": len(text.encode("utf-8")),
            "bytes_out": len(out.encode("utf-8")),
            "method": method,
            "aggressive": args.aggressive,
            "trace": trace,
            "compressed": out,
        }
        sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2)).encode("utf-8"))
        return

    report(text, out, t_in, t_out, trace, method,
           price_in=args.price_in, sends=args.sends)
    if args.diff:
        sys.stdout.buffer.write(("  --- texto comprimido ---\n" + out + "\n").encode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
