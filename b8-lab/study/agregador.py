# -*- coding: utf-8 -*-
"""
B8 Lab · agregador del estudio multi-usuario.

Junta los JSON de métricas que mandaron los participantes (solo números, sin datos
personales) y produce la DISTRIBUCIÓN: la evidencia que convierte el n=1 en algo
serio para el plan de B8.

Uso:
    1. Guarda cada JSON recibido en  b8-lab/study/resultados/  (un .json por persona)
    2. python b8-lab/study/agregador.py
Salida: b8-lab/study/REPORTE_ESTUDIO.md  +  resumen en consola.
"""
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES_DIR = HERE / "resultados"
REPORT = HERE / "REPORTE_ESTUDIO.md"

FIELDS = [
    ("ahorro_texto_pct", "Ahorro en texto %"),
    ("neto_amortizado_pct", "Neto amortizado %"),
    ("punto_equilibrio", "Punto de equilibrio (x)"),
    ("codebook_entradas", "Entradas del codebook"),
    ("tokens", "Tamaño (tokens)"),
]


def summ(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    if not vals:
        return None
    return {
        "n": len(vals),
        "media": round(st.mean(vals), 1),
        "mediana": round(st.median(vals), 1),
        "min": round(min(vals), 1),
        "max": round(max(vals), 1),
    }


def main():
    RES_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(RES_DIR.glob("*.json"))
    rows = []
    for f in files:
        try:
            rows.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"  (salto {f.name}: {e})", file=sys.stderr)

    def w(s):
        sys.stdout.buffer.write((s + "\n").encode("utf-8", errors="replace"))

    if not rows:
        w(f"\nNo hay resultados todavía. Pon los .json en {RES_DIR} y vuelve a correr.")
        return

    w(f"\n  B8 · Estudio multi-usuario — {len(rows)} participantes")
    w("  " + "-" * 48)
    L = []
    L.append(f"# B8 — Reporte del estudio multi-usuario\n")
    L.append(f"**Participantes:** {len(rows)} · solo métricas anónimas (cero datos personales)\n")
    L.append("## Distribución\n")
    L.append("| Métrica | n | media | mediana | min | max |")
    L.append("|---|--:|--:|--:|--:|--:|")
    for key, label in FIELDS:
        s = summ([r.get(key) for r in rows])
        if not s:
            continue
        L.append(f"| {label} | {s['n']} | {s['media']} | {s['mediana']} | {s['min']} | {s['max']} |")
        w(f"  {label:<26} media {s['media']:>6}  mediana {s['mediana']:>6}  (n={s['n']})")

    # cuántos dieron ahorro neto positivo
    pos = sum(1 for r in rows if isinstance(r.get("neto_amortizado_pct"), (int, float))
              and r["neto_amortizado_pct"] > 0)
    L.append(f"\n## Lectura\n")
    L.append(f"- **{pos}/{len(rows)}** participantes tuvieron ahorro neto amortizado **positivo**.")
    L.append("- Recordatorio honesto: esto mide el codebook determinista (Escalón 0) sobre datos "
             "reales y diversos. El salto grande (taquigrafía zero-shot, ~48% en el Escalón 0.5) "
             "se mide aparte con un modelo en el loop.")
    L.append("- Próximo: con esta distribución, el Plan de B8 puede decir números reales en vez "
             "de un solo caso.")

    REPORT.write_text("\n".join(L), encoding="utf-8")
    w(f"  {pos}/{len(rows)} con ahorro neto positivo")
    w(f"  -> {REPORT.name}")


if __name__ == "__main__":
    main()
