# -*- coding: utf-8 -*-
"""
Brevia · B8 shorthand (capa de 2 niveles) — la fusión Brevia + B8.

Del lab B8 (b8-lab/) salió el hallazgo: la taquigrafía nativa de un LLM se
decodifica a ciegas por otro LLM (~52% compresión, ~95% fidelidad, n=3), PERO
pierde los términos duros (acrónimos nuevos, nombres propios). Este módulo es
la versión producto de la arquitectura de 2 capas validada en E2:

  Capa 1 · TAQUIGRAFÍA   → la escribe el LLM (zero-shot, lossy controlado)
  Capa 2 · CODEBOOK      → términos duros blindados como @n (determinista,
                           sin pérdida, persistente y CACHEABLE)

La lección económica del Escalón 0: el codebook solo compensa si se cachea,
nunca si viaja en cada mensaje. Por eso aquí es un almacén persistente
(~/.brevia/codebook.json) con códigos ESTABLES entre sesiones: @7 significa
lo mismo hoy y mañana, y el libro crece con el uso (el "idioma personal").

Uso CLI:
  python shorthand.py pack  --text "..."   # blinda términos + instrucción p/ LLM
  python shorthand.py unpack --text "..."  # restaura los @n de una taquigrafía
  python shorthand.py book                 # muestra el codebook aprendido

Sin dependencias externas (tiktoken opcional vía compress.py).
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compress  # conteo de tokens + pre-pase seguro (dedup sin pérdida)

CODE_PREFIX = "@"
STORE_PATH = Path.home() / ".brevia" / "codebook.json"
MAX_TERMS_PER_PACK = 20

# Palabras comunes que empiezan con mayúscula por ir al inicio de frase — NO son
# nombres propios; no deben gastar una entrada del codebook.
COMMON = {
    "hola", "gracias", "buenas", "saludos", "compra", "vende", "revisa", "analiza",
    "necesito", "quiero", "puedes", "ayuda", "ayúdame", "por", "para", "favor", "dato",
    "documento", "el", "la", "los", "las", "un", "una", "este", "esta", "eso", "como",
    "pero", "si", "no", "ahora", "luego", "hi", "hello", "hey", "thanks", "please",
    "ok", "yes", "the", "this", "that", "you", "we", "i", "a", "an", "and", "or",
}


def detect_hard_terms(text):
    """Solo lo de ALTA confianza que carga señal no adivinable: términos entre
    comillas, acrónimos/códigos, y nombres propios reales. Dedup de subpartes."""
    cands = []  # (term, sector) en orden de confianza

    # 1. términos entre comillas (alta confianza)
    for m in re.findall(r"['\"]([^'\"]{2,40})['\"]", text):
        cands.append((m.strip(), "cita/term"))
    # 2. acrónimos y códigos alfanuméricos: B8, SPY, LLC, GPT-4 (alta confianza)
    for m in re.findall(r"\b[A-Z][A-Z0-9]*[0-9A-Z](?:-[A-Z0-9]+)?\b", text):
        if len(m) >= 2 and not m.isdigit():
            cands.append((m, "acrónimo/código"))
    # 3. nombres compuestos: Mayúscula Mayúscula (Mrs Lima, Lewis Jackson).
    # Se recortan palabras comunes en los bordes ("Hola Miguel" -> "Miguel").
    for m in re.findall(r"\b[A-Z][a-záéíóúñ]+(?:\s+[A-Z][a-záéíóúñ]+)+\b", text):
        words = m.strip().split()
        while words and words[0].lower() in COMMON:
            words.pop(0)
        while words and words[-1].lower() in COMMON:
            words.pop()
        if len(words) >= 2:
            cands.append((" ".join(words), "nombre compuesto"))
    # 4. nombres propios sueltos: Mayúscula + minúsculas, no común, >=4 letras
    for m in re.findall(r"\b[A-Z][a-záéíóúñ]{3,}\b", text):
        if m.lower() not in COMMON:
            cands.append((m, "nombre propio"))

    chosen = {}
    for term, sector in cands:
        if term in chosen:
            continue
        # si el término es una palabra contenida en uno ya elegido más largo, saltar
        if any(term != t and re.search(r"\b" + re.escape(term) + r"\b", t) for t in chosen):
            continue
        chosen[term] = sector
    return chosen


class ShorthandBook:
    """Codebook sectorial persistente: término duro ←→ código @n estable.

    Los códigos nunca se reciclan (un @n emitido significa siempre lo mismo),
    así una taquigrafía guardada ayer se expande bien mañana."""

    def __init__(self, path=STORE_PATH):
        self.path = Path(path)
        self.data = {"version": 1, "next": 1, "terms": {}}  # code -> {term, sector, uses}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass  # almacén corrupto: se rehace sin tumbar la herramienta
        self._by_term = {v["term"]: c for c, v in self.data["terms"].items()}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=1),
                             encoding="utf-8")

    def code_for(self, term, sector):
        """Devuelve el código estable del término; lo aprende si es nuevo."""
        if term in self._by_term:
            code = self._by_term[term]
            self.data["terms"][code]["uses"] += 1
            return code
        code = f"{CODE_PREFIX}{self.data['next']}"
        self.data["next"] += 1
        self.data["terms"][code] = {"term": term, "sector": sector, "uses": 1}
        self._by_term[term] = code
        return code

    def shield(self, text, max_terms=MAX_TERMS_PER_PACK):
        """Blinda los términos duros del texto como @n. Devuelve (texto, sub-book)."""
        terms = detect_hard_terms(text)
        # los más largos primero: mayor valor de proteger y reemplazo sin colisión
        ordered = sorted(terms.items(), key=lambda kv: -len(kv[0]))[:max_terms]
        used = {}
        out = text
        for term, sector in ordered:
            code = self.code_for(term, sector)
            # lookaround en vez de \b: aguanta términos que terminan en símbolo
            out, n = re.subn(r"(?<!\w)" + re.escape(term) + r"(?!\w)", code, out)
            if n:
                used[code] = self.data["terms"][code]
        if used:
            self._save()
        return out, used

    def restore(self, text):
        """Restaura TODOS los códigos @n conocidos a su término exacto."""
        found = re.findall(re.escape(CODE_PREFIX) + r"\d+", text)
        missing = []
        # números más largos primero para que @12 no lo pise @1
        for code in sorted(set(found), key=lambda c: -len(c)):
            info = self.data["terms"].get(code)
            if info:
                text = text.replace(code, info["term"])
                info["uses"] += 1
            else:
                missing.append(code)
        if found:
            self._save()
        return text, missing

    def block(self, subset=None):
        """El codebook como bloque de texto (lo que se cachea, no viaja por mensaje)."""
        items = subset if subset is not None else self.data["terms"]
        if not items:
            return "(codebook vacío)"
        return "Términos:\n" + "\n".join(
            f"{c}={v['term']}" for c, v in sorted(
                items.items(), key=lambda kv: int(kv[0][len(CODE_PREFIX):])))


# --------------------------------------------------------------------------- #
# Instrucciones para la capa 1 (el LLM escribe/expande la taquigrafía)
# --------------------------------------------------------------------------- #
ENCODE_INSTRUCTION = (
    "Reescribe el texto siguiente en tu taquigrafía semántica más densa: "
    "abreviaturas, símbolos y fusiones que TÚ mismo (u otro LLM) puedas "
    "reconstruir sin glosario. Conserva INTACTOS los códigos @n y cualquier "
    "bloque de código, cifra o negación. Devuelve solo la taquigrafía."
)
DECODE_INSTRUCTION = (
    "El texto siguiente es taquigrafía semántica densa escrita por un LLM. "
    "Reconstrúyelo en lenguaje natural completo, fiel a cada idea. Los códigos "
    "@n ya fueron restaurados a sus términos exactos: no los alteres."
)


def pack(text, book=None, safe_compress=True, counter=None):
    """Capa 2 completa: dedup seguro + blindaje de términos. Deja el texto listo
    para que el LLM escriba la taquigrafía (capa 1)."""
    book = book or ShorthandBook()
    shielded, used = book.shield(text)
    if safe_compress:
        shielded, _, _, _ = compress.compress(shielded, aggressive=False, counter=counter)
    return {"text": shielded, "book": used, "book_block": book.block(used)}


def expand(text, book=None):
    """Restaura los términos duros de una taquigrafía. La expansión del lenguaje
    general la hace el LLM (zero-shot, sin glosario)."""
    book = book or ShorthandBook()
    restored, missing = book.restore(text)
    return {"text": restored, "missing": missing}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _read_input(args):
    if args.text:
        return args.text
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def main():
    ap = argparse.ArgumentParser(description="Brevia · B8 shorthand (2 capas)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("pack", "unpack"):
        p = sub.add_parser(name)
        p.add_argument("--text", help="texto directo")
        p.add_argument("--file", help="leer de archivo")
        if name == "pack":
            p.add_argument("--no-compress", action="store_true",
                           help="no aplicar el dedup seguro antes del blindaje")
    sub.add_parser("book", help="muestra el codebook aprendido")
    args = ap.parse_args()

    def w(s):
        sys.stdout.buffer.write((s + "\n").encode("utf-8", errors="replace"))

    counter, method = compress._tiktoken_counter()

    def count(t):
        return compress.count_tokens(t, counter)

    if args.cmd == "book":
        book = ShorthandBook()
        terms = book.data["terms"]
        w(f"  codebook personal · {len(terms)} términos · {book.path}")
        by_sector = {}
        for c, v in terms.items():
            by_sector.setdefault(v["sector"], []).append((c, v))
        for sector, items in sorted(by_sector.items()):
            w(f"  [{sector}]")
            for c, v in sorted(items, key=lambda kv: -kv[1]["uses"]):
                w(f"    {c} = {v['term']}  (x{v['uses']})")
        return

    text = _read_input(args)
    if not text.strip():
        w("(sin texto: usa --text, --file o stdin)")
        return

    if args.cmd == "pack":
        r = pack(text, safe_compress=not args.no_compress, counter=counter)
        t_in, t_out = count(text), count(r["text"])
        cb = count(r["book_block"]) if r["book"] else 0
        w(f"\n  Brevia · shorthand pack — capa 2 lista, capa 1 la escribe el LLM")
        w("  " + "-" * 60)
        w(f"  tokens: {t_in} -> {t_out} (términos blindados: {len(r['book'])} · "
          f"codebook {cb} tok, se cachea 1 vez)")
        if r["book"]:
            w("\n" + r["book_block"])
        w("\n--- INSTRUCCIÓN PARA EL LLM ---")
        w(ENCODE_INSTRUCTION)
        w("\n--- TEXTO ---")
        w(r["text"])
    else:  # unpack
        r = expand(text)
        if r["missing"]:
            w(f"(códigos desconocidos: {', '.join(r['missing'])})")
        w("\n--- INSTRUCCIÓN PARA EL LLM ---")
        w(DECODE_INSTRUCTION)
        w("\n--- TAQUIGRAFÍA (términos ya restaurados) ---")
        w(r["text"])


if __name__ == "__main__":
    main()
