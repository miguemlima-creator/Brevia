# -*- coding: utf-8 -*-
"""
B8 Lab · Escalón 0 — experimento de evidencia.

Corre el motor de codebook sobre un corpus de chat real(ista) y responde la
pregunta que hace o rompe la idea: ¿el codebook ahorra tokens NETOS?

Salida: b8-lab/report.md  +  resumen en consola.
Uso:  python b8-lab/experiment.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codebook as cb  # noqa: E402

LAB = Path(__file__).resolve().parent
CORPUS_DIR = LAB / "corpus"
REPORT = LAB / "report.md"


def load_corpus():
    files = sorted(CORPUS_DIR.glob("*.txt"))
    texts = [f.read_text(encoding="utf-8") for f in files]
    full = "\n".join(texts)
    # "mensajes" = líneas no vacías con un turno (aprox. lo que llevaría el codebook)
    msgs = [l for t in texts for l in t.splitlines() if l.strip()]
    return full, len(files), len(msgs)


def main():
    full, n_files, n_msgs = load_corpus()
    book = cb.build_codebook(full, max_entries=20, min_occ=2)
    stats = cb.analyze(full, book, num_messages=n_msgs)

    # curva de amortización: el codebook es costo fijo (1 vez); el ahorro crece con
    # el volumen de la conversación (misma densidad de frases). net% -> text_savings_pct
    def amort_curve(k):
        net = k * stats["text_savings"] - stats["codebook_cost"]
        pct = net / (k * stats["raw"]) * 100 if stats["raw"] else 0
        return net, round(pct, 1)
    curve = {k: amort_curve(k) for k in (1, 2, 5, 10, 20)}

    def w(s):
        sys.stdout.buffer.write((s + "\n").encode("utf-8", errors="replace"))

    # --- consola ---
    w("\n  B8 LAB · Escalón 0 — codebook aprendido del chat")
    w("  " + "-" * 52)
    w(f"  corpus           : {n_files} sesiones · {n_msgs} mensajes · {stats['raw']} tokens")
    w(f"  codebook         : {stats['entries']} entradas · cuesta {stats['codebook_cost']} tokens")
    w(f"  ahorro en texto  : {stats['text_savings']} tokens ({stats['text_savings_pct']}%)")
    w("")
    w(f"  NETO amortizado  : {stats['amortized_net']:+d} tokens ({stats['amortized_net_pct']:+.1f}%)   <- codebook 1 vez")
    w(f"  NETO per-message : {stats['per_message_net']:+d} tokens                 <- codebook cada mensaje")
    w(f"  punto equilibrio : reusar el corpus {stats['breakeven_reuses']}x para que el codebook se pague")
    w(f"  decode lossless  : {'SI' if stats['lossless'] else 'NO'}")
    w("")
    w("  curva de amortización (net% al crecer la conversación):")
    for k, (net, pct) in curve.items():
        w(f"    x{k:>2} volumen : {net:+5d} tokens  ({pct:+.1f}%)")
    w(f"  -> {REPORT.name}")

    # --- top entradas del codebook ---
    top = sorted(book.items(), key=lambda kv: -cb.est_tokens(kv[1]))[:8]

    # --- report.md ---
    L = []
    L.append("# B8 Lab — Escalón 0: ¿un codebook aprendido del chat ahorra tokens netos?\n")
    L.append("**Hipótesis:** si observamos la interacción real y construimos un codebook "
             "(frase frecuente → código corto), ¿se ahorran tokens *incluyendo* el costo "
             "de comunicarle el codebook al modelo? Es el \"BPE de nivel superior\" de Miguel.\n")
    L.append("## Datos\n")
    L.append(f"- Corpus: **{n_files} sesiones**, {n_msgs} mensajes, **{stats['raw']} tokens** (estimados)")
    L.append(f"- Codebook: **{stats['entries']} entradas**, cuesta **{stats['codebook_cost']} tokens** comunicarlo")
    L.append(f"- Decode determinista sin pérdida: **{'sí ✅' if stats['lossless'] else 'no ❌'}**\n")
    L.append("## Resultado económico (lo que hace o rompe la idea)\n")
    L.append("| Métrica | Valor |")
    L.append("|---|---|")
    L.append(f"| Ahorro en el texto (bruto) | {stats['text_savings']} tokens ({stats['text_savings_pct']}%) |")
    L.append(f"| **Neto amortizado** (codebook 1 vez, estilo caché) | **{stats['amortized_net']:+d} tokens ({stats['amortized_net_pct']:+.1f}%)** |")
    L.append(f"| Neto per-message (codebook en cada mensaje) | {stats['per_message_net']:+d} tokens |")
    L.append(f"| Punto de equilibrio | reusar el corpus **{stats['breakeven_reuses']}x** |\n")
    L.append("## Curva de amortización\n")
    L.append("El codebook es un **costo fijo** (se comunica una vez); el ahorro crece con el "
             "volumen de la conversación. Por eso el net% sube hacia el ahorro de texto (techo) "
             "a medida que la charla se alarga:\n")
    L.append("| Volumen de conversación | Neto | Net % |")
    L.append("|---|---|---|")
    for k, (net, pct) in curve.items():
        L.append(f"| ×{k} | {net:+d} tokens | {pct:+.1f}% |")
    L.append("")
    L.append("## Codebook aprendido (top entradas)\n")
    L.append("| Código | Frase | tokens |")
    L.append("|---|---|---|")
    for code, phrase in top:
        L.append(f"| `{code}` | {phrase} | {cb.est_tokens(phrase)} |")
    L.append("")
    L.append("## Lectura honesta\n")
    verdict = []
    if stats["amortized_net"] > 0:
        verdict.append(f"En régimen **amortizado** (el codebook viaja una vez y se reusa, como el "
                       f"prompt caching), el codebook **SÍ ahorra neto: {stats['amortized_net_pct']:+.1f}%**. "
                       f"Esa es la condición de viabilidad — y se cumple.")
    else:
        verdict.append("En régimen amortizado el codebook **no ahorra neto** en este corpus: el costo "
                       "de comunicarlo supera lo que ahorra. Habría que mejorar la selección de frases "
                       "o usar un corpus con más repetición.")
    if stats["per_message_net"] <= 0:
        verdict.append("En régimen **per-message** (codebook en cada mensaje) **no compensa** — confirma "
                       "que la idea solo vive si el codebook se **cachea/reusa**, no si se reenvía cada vez.")
    verdict.append(f"El punto de equilibrio (**{stats['breakeven_reuses']}x**) dice cuántas veces hay que "
                   f"reusar el contexto para que el codebook se pague solo.")
    verdict.append("El decode determinista es sin pérdida; el **decode zero-shot por el modelo** (sin darle "
                   "el codebook entero) es la prueba fuerte y es el siguiente experimento — requiere un LLM "
                   "en el loop (lo tenemos vía el MCP de Brevia).")
    for v in verdict:
        L.append("- " + v)
    L.append("\n## Siguiente paso (Escalón 0.5)\n")
    L.append("- Probar **decode zero-shot**: darle al modelo texto codificado SIN el glosario completo y "
             "ver si lo reconstruye. Si lo logra, el codebook ni siquiera necesita viajar entero → el "
             "ahorro neto sube muchísimo.")
    L.append("- Probar con **chats reales exportados** de Miguel (su ventaja injusta) en vez del corpus de muestra.")
    L.append("- Diferenciador: que cada entrada del codebook guarde también **el porqué** (fusión con Engram).")

    REPORT.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
