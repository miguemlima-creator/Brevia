# -*- coding: utf-8 -*-
"""
Brevia LAB · benchmark

Corre el motor (../compress.py) sobre todo el corpus sintetico y reporta:
  - ahorro agregado (seguro y agresivo), promedio + mediana
  - desglose por categoria
  - de donde viene el ahorro (suma por paso)
  - CHEQUEO DE SEGURIDAD: que los bloques de codigo queden byte-identicos
  - deteccion de ahorro falso (already_tight no debe inflar)

Salida: brevia/lab/benchmark_report.md  +  benchmark_results.json
"""
import json
import re
import statistics
import sys
from pathlib import Path

# importar el motor real
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import compress  # noqa: E402

CORPUS = Path(__file__).parent / "corpus"
REPORT_MD = Path(__file__).parent / "benchmark_report.md"
REPORT_JSON = Path(__file__).parent / "benchmark_results.json"

CODE_RE = re.compile(r"```.*?```", re.DOTALL)


def code_blocks(text):
    return CODE_RE.findall(text)


def run():
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    counter, method = compress._tiktoken_counter()
    method = method or "heuristica char/4 (estimacion)"

    rows = []
    safety_violations = []

    for item in manifest["items"]:
        text = (CORPUS / item["file"]).read_text(encoding="utf-8")
        cat = item["category"]
        for mode in ("safe", "aggressive"):
            out, t_in, t_out, trace = compress.compress(
                text, aggressive=(mode == "aggressive"), counter=counter)
            saved = t_in - t_out
            pct = (saved / t_in * 100) if t_in else 0
            # chequeo de seguridad: codigo intacto
            in_code = code_blocks(text)
            out_code = code_blocks(out)
            code_ok = in_code == out_code
            if in_code and not code_ok:
                safety_violations.append({"file": item["file"], "mode": mode})
            rows.append({
                "file": item["file"], "category": cat, "mode": mode,
                "tokens_in": t_in, "tokens_out": t_out, "saved": saved,
                "pct": round(pct, 1),
                "bytes_in": len(text.encode("utf-8")),
                "bytes_out": len(out.encode("utf-8")),
                "code_blocks": len(in_code), "code_ok": code_ok,
                "trace": trace,
            })

    return rows, safety_violations, method


def agg(rows, mode, key="pct"):
    vals = [r[key] for r in rows if r["mode"] == mode]
    return vals


def by_category(rows, mode):
    cats = {}
    for r in rows:
        if r["mode"] != mode:
            continue
        c = r["category"]
        cats.setdefault(c, {"pct": [], "saved": 0, "tin": 0, "tout": 0})
        cats[c]["pct"].append(r["pct"])
        cats[c]["saved"] += r["saved"]
        cats[c]["tin"] += r["tokens_in"]
        cats[c]["tout"] += r["tokens_out"]
    return cats


def step_breakdown(rows, mode):
    steps = {}
    for r in rows:
        if r["mode"] != mode:
            continue
        for s in r["trace"]:
            steps[s["paso"]] = steps.get(s["paso"], 0) + s["ahorro"]
    return steps


def main():
    rows, violations, method = run()

    total_in = sum(r["tokens_in"] for r in rows if r["mode"] == "safe")
    total_out_safe = sum(r["tokens_out"] for r in rows if r["mode"] == "safe")
    total_out_aggr = sum(r["tokens_out"] for r in rows if r["mode"] == "aggressive")
    n = len([r for r in rows if r["mode"] == "safe"])

    safe_pct = agg(rows, "safe")
    aggr_pct = agg(rows, "aggressive")

    # ahorro falso en already_tight
    tight_safe = [r["pct"] for r in rows if r["category"] == "already_tight" and r["mode"] == "safe"]

    L = []
    L.append("# Brevia — reporte de benchmark (datos sintéticos)\n")
    L.append(f"- Corpus: **{n} prompts** sintéticos · semilla 42 (reproducible)")
    L.append(f"- Conteo de tokens: `{method}`")
    L.append(f"- Bloques de código probados: **{sum(1 for r in rows if r['code_blocks'] and r['mode']=='aggressive')}** · "
             f"violaciones de seguridad: **{len(violations)}**\n")

    L.append("## Resultado global\n")
    L.append("| Modo | Tokens totales | Ahorro total | Ahorro medio | Mediana |")
    L.append("|---|---|---|---|---|")
    L.append(f"| Seguro | {total_in:,} → {total_out_safe:,} | "
             f"{total_in-total_out_safe:,} ({(total_in-total_out_safe)/total_in*100:.1f}%) | "
             f"{statistics.mean(safe_pct):.1f}% | {statistics.median(safe_pct):.1f}% |")
    L.append(f"| Agresivo | {total_in:,} → {total_out_aggr:,} | "
             f"{total_in-total_out_aggr:,} ({(total_in-total_out_aggr)/total_in*100:.1f}%) | "
             f"{statistics.mean(aggr_pct):.1f}% | {statistics.median(aggr_pct):.1f}% |\n")

    L.append("## Ahorro por categoría (modo seguro)\n")
    L.append("| Categoría | Tokens | Ahorro | % medio |")
    L.append("|---|---|---|---|")
    cats = by_category(rows, "safe")
    for c in sorted(cats, key=lambda k: -statistics.mean(cats[k]["pct"])):
        d = cats[c]
        L.append(f"| {c} | {d['tin']:,} → {d['tout']:,} | {d['saved']:,} | {statistics.mean(d['pct']):.1f}% |")
    L.append("")

    L.append("## De dónde viene el ahorro (suma de tokens por paso)\n")
    L.append("**Modo seguro:**")
    for paso, ahorro in sorted(step_breakdown(rows, "safe").items(), key=lambda x: -x[1]):
        L.append(f"- `{paso}` → {ahorro:,} tokens")
    L.append("\n**Pasos extra del modo agresivo:**")
    aggr_steps = step_breakdown(rows, "aggressive")
    safe_steps = step_breakdown(rows, "safe")
    for paso in ("quitar_relleno", "reducir_decoracion"):
        if paso in aggr_steps:
            L.append(f"- `{paso}` → {aggr_steps[paso]:,} tokens")
    L.append("")

    L.append("## Chequeos de calidad\n")
    L.append(f"- **Seguridad de código:** {'✅ todos los bloques de código intactos' if not violations else '❌ ' + str(len(violations)) + ' violaciones'}")
    tight_max = max(tight_safe) if tight_safe else 0
    L.append(f"- **Ahorro falso (already_tight):** máx {tight_max:.1f}% en prompts ya óptimos "
             f"{'✅ (bajo, no inflamos)' if tight_max < 15 else '⚠️ revisar'}")
    L.append("")

    L.append("## Lectura honesta\n")
    L.append("El ahorro grande se concentra en `duplicated_ctx` y `long_document` "
             "(no reenviar lo mismo) — confirma que el valor real está en lo **estructural**, "
             "no en recortar palabras. Los prompts ya óptimos (`already_tight`) casi no cambian, "
             "que es lo correcto: la herramienta no debe inventar ahorro.\n")

    REPORT_MD.write_text("\n".join(L), encoding="utf-8")
    REPORT_JSON.write_text(json.dumps({
        "n": n, "method": method, "violations": violations,
        "global": {
            "tokens_in": total_in,
            "tokens_out_safe": total_out_safe,
            "tokens_out_aggressive": total_out_aggr,
            "safe_mean_pct": round(statistics.mean(safe_pct), 2),
            "aggr_mean_pct": round(statistics.mean(aggr_pct), 2),
        },
        "rows": rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # consola
    def w(s):
        sys.stdout.buffer.write((s + "\n").encode("utf-8", errors="replace"))

    w(f"\nBenchmark: {n} prompts | metodo {method}")
    w(f"  SEGURO   : {total_in:,} -> {total_out_safe:,}  ({(total_in-total_out_safe)/total_in*100:.1f}% | medio {statistics.mean(safe_pct):.1f}%)")
    w(f"  AGRESIVO : {total_in:,} -> {total_out_aggr:,}  ({(total_in-total_out_aggr)/total_in*100:.1f}% | medio {statistics.mean(aggr_pct):.1f}%)")
    w(f"  codigo intacto: {'SI' if not violations else 'NO ('+str(len(violations))+' fallos)'}")
    w(f"  ahorro falso (already_tight) max: {tight_max:.1f}%")
    w(f"  -> {REPORT_MD.name}  +  {REPORT_JSON.name}")


if __name__ == "__main__":
    main()
