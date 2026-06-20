# -*- coding: utf-8 -*-
"""
B8 Lab · motor de codebook (Escalón 0)

Hipótesis a probar: si observamos la interacción real del chat y construimos un
"codebook" (frase frecuente -> código corto), ¿se ahorran tokens **netos**, es
decir, incluyendo el costo de tener que comunicarle el codebook al modelo?

Esto es el "BPE de nivel superior" de Miguel: en vez de fusionar caracteres
frecuentes, fusionamos FRASES/conceptos frecuentes del corpus en códigos cortos.

Dos regímenes honestos:
  - per-message : el codebook viaja en CADA mensaje (cuesta cada vez)
  - amortizado  : el codebook viaja UNA vez y se reusa (estilo prompt caching)

El decode es determinista y sin pérdida (lookup). El "decode zero-shot por el
modelo" (sin darle el codebook entero) es la prueba fuerte y se hace aparte con un
LLM real — aquí medimos primero la economía, que es lo que hace o rompe la idea.

Sin dependencias externas.
"""
import re
from collections import Counter

# código: símbolo raro + número. Elegido para tokenizar corto y no chocar con texto.
CODE_PREFIX = "§"


def est_tokens(text):
    """Estimación consistente con Brevia (char/4 promediado con palabras/0.75)."""
    chars = len(text)
    words = len(re.findall(r"\S+", text))
    return max(0, int(round((chars / 4 + words / 0.75) / 2)))


_WORD = re.compile(r"\w+", re.UNICODE)


def _norm_spaces(s):
    return re.sub(r"\s+", " ", s).strip()


def mine_phrases(corpus, n_min=2, n_max=7, min_occ=2):
    """Cuenta n-gramas de palabras y estima su potencial de ahorro (lado texto).
    Devuelve lista de dicts ordenada por ahorro potencial bruto."""
    # trabajamos sobre el texto en minúsculas para contar, pero guardamos forma original
    lower = corpus.lower()
    words = _WORD.findall(lower)
    counts = Counter()
    for n in range(n_min, n_max + 1):
        for i in range(len(words) - n + 1):
            counts[" ".join(words[i:i + n])] += 1

    code_tok = est_tokens(CODE_PREFIX + "99")  # costo típico de un código
    out = []
    for phrase, occ in counts.items():
        if occ < min_occ:
            continue
        ptok = est_tokens(phrase)
        if ptok <= code_tok:
            continue  # no vale la pena codificar algo tan corto
        gross = occ * (ptok - code_tok)
        out.append({"phrase": phrase, "occ": occ, "ptok": ptok, "gross": gross})
    out.sort(key=lambda d: -d["gross"])
    return out


def _trigrams(phrase):
    """Conjunto de trigramas de palabras (para detectar frases solapadas/shingles)."""
    w = phrase.split()
    if len(w) < 3:
        return {tuple(w)}
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


def build_codebook(corpus, max_entries=20, n_min=2, n_max=7, min_occ=2):
    """Selección greedy evitando solapamiento. Descarta una frase candidata si es
    subcadena de una elegida O si comparte un trigrama de palabras con ella (eso
    mata los 'shingles' — fragmentos corridos de la misma oración repetida, que
    desperdiciarían entradas del codebook). Devuelve dict {codigo: frase}."""
    candidates = mine_phrases(corpus, n_min, n_max, min_occ)
    chosen = []
    chosen_tri = set()
    for c in candidates:
        p = c["phrase"]
        tri = _trigrams(p)
        if tri & chosen_tri:
            continue
        if any(p in q or q in p for q in chosen):
            continue
        chosen.append(p)
        chosen_tri |= tri
        if len(chosen) >= max_entries:
            break
    # asignar códigos: las más largas primero (para reemplazo sin colisión)
    chosen.sort(key=len, reverse=True)
    return {f"{CODE_PREFIX}{i+1}": p for i, p in enumerate(chosen)}


def _phrase_regex(phrase):
    # coincide la frase como secuencia de palabras, ignorando diferencias de espacios
    parts = [re.escape(w) for w in phrase.split()]
    return re.compile(r"\b" + r"\s+".join(parts) + r"\b", re.IGNORECASE)


def encode(text, codebook):
    """Reemplaza las frases por sus códigos. Frases largas primero."""
    items = sorted(codebook.items(), key=lambda kv: -len(kv[1]))
    out = text
    for code, phrase in items:
        out = _phrase_regex(phrase).sub(code, out)
    return out


def decode(text, codebook):
    """Reemplaza los códigos por las frases (determinista, lossless en estructura)."""
    out = text
    # reemplazar códigos de mayor número primero evita que §1 toque §10
    for code in sorted(codebook, key=lambda c: -int(c[len(CODE_PREFIX):])):
        out = out.replace(code, codebook[code])
    return out


def codebook_block(codebook):
    """Cómo se le comunicaría el codebook al modelo (texto que cuesta tokens)."""
    lines = [f"{code}={phrase}" for code, phrase in codebook.items()]
    return "Glosario:\n" + "\n".join(lines)


def analyze(corpus, codebook, num_messages=None):
    """Economía honesta del codebook sobre un corpus."""
    enc = encode(corpus, codebook)
    raw = est_tokens(corpus)
    encoded = est_tokens(enc)
    text_savings = raw - encoded
    cb_cost = est_tokens(codebook_block(codebook))

    amortized_net = text_savings - cb_cost          # codebook 1 sola vez
    # per-message: el codebook viaja en cada mensaje
    n = num_messages or 1
    per_msg_net = text_savings - cb_cost * n

    # punto de equilibrio: ¿cuántas "copias del corpus" hay que reusar para que
    # el codebook se pague, si viajara cada vez? (text_savings por copia vs cb_cost)
    breakeven_reuses = (cb_cost / text_savings) if text_savings > 0 else float("inf")

    # chequeo de pérdida: decode(encode(x)) debe recuperar el texto (ignorando
    # diferencias de espacios/mayúsculas que introduce el matching)
    restored = decode(enc, codebook)
    lossless = _norm_spaces(restored.lower()) == _norm_spaces(corpus.lower())

    return {
        "raw": raw, "encoded": encoded, "text_savings": text_savings,
        "text_savings_pct": round(text_savings / raw * 100, 1) if raw else 0,
        "codebook_cost": cb_cost, "entries": len(codebook),
        "amortized_net": amortized_net,
        "amortized_net_pct": round(amortized_net / raw * 100, 1) if raw else 0,
        "per_message_net": per_msg_net,
        "breakeven_reuses": round(breakeven_reuses, 2),
        "lossless": lossless,
    }
