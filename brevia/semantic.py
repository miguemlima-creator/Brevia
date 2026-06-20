# -*- coding: utf-8 -*-
"""
Brevia · compresión semántica extractiva (B4) — sin GPU, sin red, stdlib.

⚠️ LOSSY a propósito: a diferencia del dedup (sin pérdida), esto RESUME — descarta
las frases de menor información para alcanzar un ratio objetivo. Es opt-in y se
controla con --keep (cuánto conservar). No es un modelo neuronal (eso sería un
LLMLingua con GPU); es extractivo estadístico — un escalón real por encima del
recorte de relleno por reglas, manteniendo la filosofía "sin GPU".

Cómo puntúa cada frase:
  + frecuencia de sus palabras de contenido (TF, sin stopwords ES/EN)
  + bonus si está al inicio (suele traer la tesis)
  + SIEMPRE conserva: frases con código, con números/cifras, y preguntas
  - penaliza frases muy cortas o de puro relleno

Conserva el orden original. Protege bloques de código intactos.
"""
import argparse
import math
import re
import sys
from pathlib import Path

STOPWORDS = set("""
de la que el en y a los del se las por un para con no una su al lo como mas pero
sus le ya o este si porque esta entre cuando muy sin sobre tambien me hasta hay
donde quien desde todo nos durante todos uno les ni contra otros ese eso ante
ellos e esto mi antes algunos que unos yo otro otras otra el tanto esa estos mucho
quienes nada muchos cual sea poco ella estar haber estas estaba estamos
the of to and a in is it you that he was for on are with as i his they be at one
have this from or had by hot but some what there we can out other were all your
when up use word how said an each she which do their time if will way about many
then them would write like so these her long make thing see him two has look more
""".split())

CODE_VAULT_RE = re.compile(r"```.*?```|`[^`]+`", re.DOTALL)
NUM_RE = re.compile(r"\d")
WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,}")


def _est_tokens(text):
    chars = len(text)
    words = len(re.findall(r"\S+", text))
    return int(round((chars / 4 + words / 0.75) / 2))


def split_sentences(text):
    """Divide en frases conservando los delimitadores. Simple pero robusto."""
    parts = re.split(r"(?<=[\.\!\?])\s+|\n+", text)
    return [p for p in parts if p is not None]


def compress_semantic(text, keep=0.7):
    """keep = fracción de tokens a conservar (0.7 = quita ~30%). Devuelve dict."""
    t_in = _est_tokens(text)

    # 1) proteger código
    vault = []
    def stash(m):
        vault.append(m.group(0)); return f"\x00\x00CODE{len(vault)-1}\x00\x00"
    body = CODE_VAULT_RE.sub(stash, text)

    sents = split_sentences(body)
    if len(sents) <= 2:
        return {"text": text, "tokens_in": t_in, "tokens_out": t_in,
                "saved": 0, "kept": len(sents), "total": len(sents), "lossy": True}

    # 2) frecuencia de términos de contenido
    freq = {}
    for s in sents:
        for w in WORD_RE.findall(s.lower()):
            if w not in STOPWORDS:
                freq[w] = freq.get(w, 0) + 1

    # 3) puntuar cada frase
    scored = []
    n = len(sents)
    for i, s in enumerate(sents):
        words = [w for w in WORD_RE.findall(s.lower()) if w not in STOPWORDS]
        base = sum(freq.get(w, 0) for w in words)
        base = base / (len(words) + 1)            # normalizar por longitud
        if i < 2:
            base *= 1.5                            # bonus a las primeras frases
        force = bool(
            "\x00\x00CODE" in s or NUM_RE.search(s) or s.strip().endswith("?")
        )
        scored.append({"i": i, "text": s, "score": base, "force": force,
                       "tokens": _est_tokens(s)})

    # 4) seleccionar hasta el presupuesto de tokens (forzadas siempre entran)
    budget = max(1, int(t_in * keep))
    chosen = set()
    used = 0
    # primero las forzadas
    for s in scored:
        if s["force"]:
            chosen.add(s["i"]); used += s["tokens"]
    # luego por score hasta llenar el presupuesto
    for s in sorted(scored, key=lambda x: -x["score"]):
        if s["i"] in chosen:
            continue
        if used + s["tokens"] <= budget:
            chosen.add(s["i"]); used += s["tokens"]

    # 5) reconstruir en orden original
    kept = [s["text"] for s in scored if s["i"] in chosen]
    out = " ".join(kept)
    # restaurar código
    out = re.sub(r"\x00\x00CODE(\d+)\x00\x00", lambda m: vault[int(m.group(1))], out)
    t_out = _est_tokens(out)
    return {"text": out, "tokens_in": t_in, "tokens_out": t_out,
            "saved": t_in - t_out, "kept": len(chosen), "total": n, "lossy": True}


def main():
    ap = argparse.ArgumentParser(description="Brevia — compresión semántica extractiva (LOSSY)")
    ap.add_argument("--file"); ap.add_argument("--text")
    ap.add_argument("--keep", type=float, default=0.7, help="fracción a conservar (0.7=quita 30 pct)")
    ap.add_argument("--diff", action="store_true")
    args = ap.parse_args()
    text = (Path(args.file).read_text(encoding="utf-8", errors="replace") if args.file
            else args.text if args.text else sys.stdin.read())
    r = compress_semantic(text, keep=args.keep)

    def w(s): sys.stdout.buffer.write((s + "\n").encode("utf-8", errors="replace"))
    pct = round(r["saved"] / r["tokens_in"] * 100, 1) if r["tokens_in"] else 0
    w(f"\n  BREVIA semántico (LOSSY · keep={args.keep})")
    w(f"  tokens : {r['tokens_in']} -> {r['tokens_out']}  (-{r['saved']} | {pct}% menos)")
    w(f"  frases : {r['kept']}/{r['total']} conservadas")
    if args.diff:
        w("  --- texto ---"); w(r["text"])


if __name__ == "__main__":
    main()
