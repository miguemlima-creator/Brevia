# -*- coding: utf-8 -*-
"""
Brevia · resumen extractivo (extractive summarization, B4) — sin GPU, sin red, stdlib.

NOMBRE HONESTO (Finding 4 de Sar): esto NO es "compresión semántica" — es **resumen
extractivo**, y es LOSSY a propósito: descarta frases enteras para alcanzar un ratio
objetivo. No es un modelo neuronal (eso sería LLMLingua con GPU); es extractivo
estadístico. Úsalo solo cuando perder detalle esté bien.

Cómo puntúa cada frase:
  + frecuencia de sus palabras de contenido (TF, sin stopwords ES/EN)
  + bonus si está al inicio (suele traer la tesis)
  + SIEMPRE conserva: código, números/cifras, preguntas, y frases de ALTO RIESGO
    (legal, plazos, obligaciones, negaciones — ver HIGH_STAKES_RE)
  - penaliza frases muy cortas o de puro relleno

⚠️ Como es lossy, devuelve y MUESTRA las frases que descarta (`dropped`) para que el
usuario verifique que no se fue nada crítico. Conserva el orden; protege el código.
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

# Patrones de ALTO RIESGO: frases que NUNCA se deben tirar aunque su score sea bajo
# (Finding 4 del reporte de Sar: el TF-scoring tiraba "cláusula de penalización" y
# "causa raíz" porque sus palabras eran poco frecuentes). Consecuencias legales,
# plazos, obligaciones y negaciones se protegen siempre.
HIGH_STAKES_RE = re.compile(
    r"\b(penalt\w*|clause|cl[áa]usula|deadline|plazo|fecha l[íi]mite|vencimiento|"
    r"contract\w*|contrato|legal|multa|sanci[óo]n\w*|fine|liabilit\w*|breach|"
    r"must|cannot|can't|do not|don't|no (?:debe|puede|pueden|deben|deberá)|"
    r"nunca|never|fail\w*|incumpl\w*|riesgo|risk|warning|urgent\w*|importante|"
    r"critical|cr[íi]tico|root cause|causa ra[íi]z)\b",
    re.IGNORECASE,
)


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
                "saved": 0, "kept": len(sents), "total": len(sents),
                "dropped": [], "lossy": True}

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
            or HIGH_STAKES_RE.search(s)        # protege frases de alto riesgo (Finding 4)
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
    # frases descartadas (Finding 4: el usuario DEBE poder verlas, no se tiran en silencio)
    def _restore(t):
        return re.sub(r"\x00\x00CODE(\d+)\x00\x00", lambda m: vault[int(m.group(1))], t)
    dropped = [_restore(s["text"]).strip() for s in scored if s["i"] not in chosen]
    out = _restore(out)
    t_out = _est_tokens(out)
    return {"text": out, "tokens_in": t_in, "tokens_out": t_out,
            "saved": t_in - t_out, "kept": len(chosen), "total": n,
            "dropped": dropped, "lossy": True}


def main():
    ap = argparse.ArgumentParser(
        description="Brevia — resumen extractivo (extractive summarization, LOSSY)")
    ap.add_argument("--file"); ap.add_argument("--text")
    ap.add_argument("--keep", type=float, default=0.7, help="fracción a conservar (0.7=quita 30 pct)")
    ap.add_argument("--diff", action="store_true")
    args = ap.parse_args()
    text = (Path(args.file).read_text(encoding="utf-8", errors="replace") if args.file
            else args.text if args.text else sys.stdin.read())
    r = compress_semantic(text, keep=args.keep)

    def w(s): sys.stdout.buffer.write((s + "\n").encode("utf-8", errors="replace"))
    pct = round(r["saved"] / r["tokens_in"] * 100, 1) if r["tokens_in"] else 0
    w(f"\n  BREVIA resumen extractivo (LOSSY · keep={args.keep})")
    w(f"  tokens : {r['tokens_in']} -> {r['tokens_out']}  (-{r['saved']} | {pct}% menos)")
    w(f"  frases : {r['kept']}/{r['total']} conservadas")
    dropped = r.get("dropped", [])
    if dropped:
        w(f"  !! DESCARTÓ {len(dropped)} frase(s) — revisa que no sean críticas:")
        for d in dropped:
            w(f"     - {d[:100]}")
    if args.diff:
        w("  --- texto ---"); w(r["text"])


if __name__ == "__main__":
    main()
