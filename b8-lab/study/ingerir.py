# -*- coding: utf-8 -*-
"""
B8 Lab · ingestor de paquetes del prompt colector.

Toma los paquetes JSON (generados por PROMPT_colector.md en cualquier IA), los valida,
los acumula en dataset.jsonl (sin duplicar) y regenera REPORTE_B8_DATOS.md con:
  - la distribución de compresión estimada
  - el "idioma compartido": las frases recurrentes que aparecen en VARIOS paquetes
    (la pista de que emerge un codebook común entre conversaciones)

Uso:
  # opción A: pega cada paquete como un .json en  b8-lab/study/paquetes/  y corre:
  python b8-lab/study/ingerir.py
  # opción B: pásalo en línea
  python b8-lab/study/ingerir.py --json '{"fuente":"chatgpt",...}'
"""
import argparse
import hashlib
import json
import re
import statistics as st
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAQ_DIR = HERE / "paquetes"
DATASET = HERE / "dataset.jsonl"
REPORT = HERE / "REPORTE_B8_DATOS.md"

REQUIRED = ["fuente", "tokens_original_aprox", "frases_recurrentes"]

# El prompt viene en ES o EN; normalizamos las llaves a las canónicas (ES).
KEY_ALIASES = {
    "source": "fuente",
    "n_messages": "n_mensajes",
    "tokens_original_approx": "tokens_original_aprox",
    "tokens_typical_message": "tokens_original_aprox",
    "recurring_phrases": "frases_recurrentes",
    "style_note": "notas",
    "original_fragment": "fragmento_original",
    "shorthand": "taquigrafia",
    "tokens_shorthand_approx": "tokens_taquigrafia_aprox",
    "compression_pct_estimate": "compresion_pct_estimada",
    "notes": "notas",
}


def normalize_keys(pkt):
    out = {}
    for k, v in pkt.items():
        out[KEY_ALIASES.get(k, k)] = v
    return out


def _norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def load_existing():
    seen = set()
    rows = []
    if DATASET.is_file():
        for line in DATASET.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                rows.append(obj)
                seen.add(obj.get("_hash"))
            except Exception:
                pass
    return rows, seen


def packet_hash(pkt):
    key = json.dumps({k: pkt.get(k) for k in ("fragmento_original", "taquigrafia",
                                              "frases_recurrentes")},
                     ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def validate(pkt):
    missing = [k for k in REQUIRED if k not in pkt or pkt[k] in (None, "", [])]
    return missing


def collect_new_packets(inline):
    pkts = []
    if inline:
        pkts.append(json.loads(inline))
    PAQ_DIR.mkdir(parents=True, exist_ok=True)
    for f in sorted(PAQ_DIR.glob("*.json")):
        try:
            pkts.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"  (salto {f.name}: {e})", file=sys.stderr)
    return [normalize_keys(p) for p in pkts]


def write_report(rows):
    def num(key):
        return [r[key] for r in rows if isinstance(r.get(key), (int, float))]

    comp = num("compresion_pct_estimada")
    toks = num("tokens_original_aprox")

    # idioma compartido: frases que aparecen en >=2 paquetes
    phrase_docs = Counter()
    for r in rows:
        for p in set(_norm(x) for x in (r.get("frases_recurrentes") or []) if x):
            phrase_docs[p] += 1
    shared = [(p, c) for p, c in phrase_docs.most_common(30) if c >= 2]

    L = []
    L.append("# B8 — Datos acumulados (prompt colector)\n")
    L.append(f"**Paquetes:** {len(rows)}\n")
    if comp:
        L.append("## Compresión estimada (taquigrafía)\n")
        L.append(f"- media **{st.mean(comp):.1f}%** · mediana {st.median(comp):.1f}% · "
                 f"min {min(comp):.0f}% · max {max(comp):.0f}% (n={len(comp)})\n")
    if toks:
        L.append(f"- Tamaño medio analizado: {int(st.mean(toks))} tokens\n")
    L.append("## Idioma compartido (frases recurrentes en ≥2 conversaciones)\n")
    if shared:
        L.append("Estas frases se repiten entre distintos chats — son las candidatas "
                 "naturales a un codebook común:\n")
        for p, c in shared:
            L.append(f"- _{p}_ — en {c} paquetes")
    else:
        L.append("(aún no hay frases compartidas entre ≥2 paquetes; junta más datos)")
    L.append("\n## Nota honesta\n")
    L.append("`compresion_pct_estimada` la auto-reporta la IA que generó el paquete — es "
             "una estimación, no medición exacta. La prueba dura sigue siendo el decode "
             "zero-shot a ciegas (dar la `taquigrafia` a otra IA sin el `fragmento_original`).")
    REPORT.write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="B8 — ingestor de paquetes")
    ap.add_argument("--json", help="un paquete JSON en línea")
    args = ap.parse_args()

    rows, seen = load_existing()
    added = 0
    for pkt in collect_new_packets(args.json):
        miss = validate(pkt)
        if miss:
            print(f"  (paquete inválido, faltan {miss}) — salto", file=sys.stderr)
            continue
        h = packet_hash(pkt)
        if h in seen:
            continue
        pkt["_hash"] = h
        with DATASET.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(pkt, ensure_ascii=False) + "\n")
        rows.append(pkt)
        seen.add(h)
        added += 1

    write_report(rows)

    def w(s):
        sys.stdout.buffer.write((s + "\n").encode("utf-8", errors="replace"))

    w(f"\nB8 ingestor: +{added} paquetes nuevos · total {len(rows)}")
    comp = [r["compresion_pct_estimada"] for r in rows
            if isinstance(r.get("compresion_pct_estimada"), (int, float))]
    if comp:
        w(f"  compresión media: {st.mean(comp):.1f}%  (n={len(comp)})")
    w(f"  -> {DATASET.name}  +  {REPORT.name}")


if __name__ == "__main__":
    main()
