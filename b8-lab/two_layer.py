# -*- coding: utf-8 -*-
"""
B8 · E2 — prototipo de 2 capas: taquigrafía + codebook sectorial.

El hallazgo del Escalón 0.5: la taquigrafía nativa del modelo se decodifica a ciegas
(~47%) PERO pierde los nombres propios / acrónimos nuevos (ej. "B8" se adivinó mal).
Solución (esta capa 2): un codebook MÍNIMO de esos términos duros, que se cachea una
vez y los recupera SIN pérdida.

  Capa 1 · TAQUIGRAFÍA  → lenguaje general (la hace el LLM, ~47%, zero-shot)
  Capa 2 · CODEBOOK SECTORIAL → nombres propios + jerga (determinista, cacheado)

Este prototipo construye y prueba la CAPA 2 (la nueva, determinista y verificable) y
estima la economía combinada. La capa 1 (taquigrafía del LLM) se representa con el
compresor por reglas como proxy, claramente etiquetado.

Sin dependencias externas.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brevia"))
import compress  # proxy de la capa de taquigrafía (la real la hace el LLM)

CODE = "@"  # marcador de término duro: @1, @2...


def est_tokens(t):
    chars = len(t); words = len(re.findall(r"\S+", t))
    return max(0, int(round((chars / 4 + words / 0.75) / 2)))


# --- detección de "términos duros" (lo que la taquigrafía NO puede adivinar) ---
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
    """Solo lo de ALTA confianza que carga señal no adivinable: acrónimos/códigos,
    términos entre comillas, y nombres propios reales. Dedup de subpartes."""
    cands = []  # (term, sector) en orden de confianza

    # 1. términos entre comillas (alta confianza)
    for m in re.findall(r"['\"]([^'\"]{2,40})['\"]", text):
        cands.append((m.strip(), "cita/term"))
    # 2. acrónimos y códigos alfanuméricos: B8, SPY, LLC, GPT-4 (alta confianza)
    for m in re.findall(r"\b[A-Z][A-Z0-9]*[0-9A-Z](?:-[A-Z0-9]+)?\b", text):
        if len(m) >= 2 and not m.isdigit():
            cands.append((m, "acrónimo/código"))
    # 3. nombres compuestos: Mayúscula Mayúscula (Mrs Lima, Lewis Jackson)
    for m in re.findall(r"\b[A-Z][a-záéíóúñ]+(?:\s+[A-Z][a-záéíóúñ]+)+\b", text):
        cands.append((m.strip(), "nombre compuesto"))
    # 4. nombres propios sueltos: Mayúscula + minúsculas, no común, >=4 letras
    for m in re.findall(r"\b[A-Z][a-záéíóúñ]{3,}\b", text):
        if m.lower() not in COMMON:
            cands.append((m, "nombre propio"))

    # dedup conservando el de mayor confianza/longitud; descartar subpartes de uno ya elegido
    chosen = {}
    for term, sector in cands:
        if term in chosen:
            continue
        # si el término es una palabra contenida en uno ya elegido más largo, saltar
        if any(term != t and re.search(r"\b" + re.escape(term) + r"\b", t) for t in chosen):
            continue
        chosen[term] = sector
    return chosen


def build_sector_codebook(text, max_terms=20):
    terms = detect_hard_terms(text)
    # ordenar: los más largos/raros primero (mayor valor de proteger)
    ordered = sorted(terms.items(), key=lambda kv: -len(kv[0]))[:max_terms]
    # códigos asignados a los más largos primero para reemplazo sin colisión
    book = {}
    for i, (term, sector) in enumerate(ordered, 1):
        book[f"{CODE}{i}"] = {"term": term, "sector": sector}
    return book


def protect(text, book):
    """Reemplaza los términos duros por sus códigos (los blinda antes de la taquigrafía)."""
    items = sorted(book.items(), key=lambda kv: -len(kv[1]["term"]))
    out = text
    for code, info in items:
        out = re.sub(r"\b" + re.escape(info["term"]) + r"\b", code, out)
    return out


def expand(text, book):
    out = text
    for code in sorted(book, key=lambda c: -int(c[len(CODE):])):
        out = out.replace(code, book[code]["term"])
    return out


def codebook_block(book):
    return "Términos:\n" + "\n".join(f"{c}={v['term']}" for c, v in book.items())


def run(text):
    book = build_sector_codebook(text)
    protected = protect(text, book)
    # capa 1 (proxy): comprimir el lenguaje general ya con los términos blindados
    shorthand_proxy, t_in_p, t_out_p, _ = compress.compress(protected, aggressive=True)
    # decode: expandir los códigos -> términos duros vuelven EXACTOS
    restored_terms = expand(shorthand_proxy, book)

    raw = est_tokens(text)
    cb_cost = est_tokens(codebook_block(book))
    payload = est_tokens(shorthand_proxy)  # lo que viaja por mensaje (sin el codebook)

    # ¿se recuperan todos los términos duros? (lo que la taquigrafía sola perdería)
    recovered = sum(1 for c, v in book.items() if v["term"] in restored_terms)

    return {
        "book": book, "raw": raw, "cb_cost": cb_cost, "payload": payload,
        "terms": len(book), "recovered": recovered,
        "shorthand_proxy": shorthand_proxy,
    }


def main():
    sample = (sys.stdin.read() if not sys.stdin.isatty() else
              "Hola Miguel, por favor analiza esto con ChatGPT para el proyecto B8. "
              "Compra opciones de SPY (calls y puts) y revisa el tax deed de la LLC en Cuba. "
              "La clase 'Mrs Lima' va en la banda azul. Gracias, sé crítico y exacto.")
    r = run(sample)

    def w(s): sys.stdout.buffer.write((s + "\n").encode("utf-8", errors="replace"))
    w("\n  B8 · E2 — 2 capas (taquigrafía + codebook sectorial)")
    w("  " + "-" * 50)
    w(f"  texto original        : {r['raw']} tokens")
    w(f"  términos duros        : {r['terms']} (blindados en codebook sectorial)")
    w(f"  codebook (1 vez, cache): {r['cb_cost']} tokens")
    w(f"  payload por mensaje   : {r['payload']} tokens (taquigrafía proxy, términos como @n)")
    w(f"  términos recuperados  : {r['recovered']}/{r['terms']}  "
      f"{'✅ sin pérdida' if r['recovered']==r['terms'] else '⚠️'}")
    w("")
    w("  codebook sectorial detectado:")
    for c, v in list(r["book"].items())[:12]:
        w(f"    {c} = {v['term']}  ({v['sector']})")
    w("")
    w("  Lectura: la taquigrafía sola perdería estos términos duros (ej. 'B8' se adivina");
    w("  mal). Blindados como @n + codebook cacheado, vuelven EXACTOS. Capa 1 (general)")
    w("  la comprime el LLM ~47%; capa 2 (estos términos) determinista y sin pérdida.")


if __name__ == "__main__":
    main()
