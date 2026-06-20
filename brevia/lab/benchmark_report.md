# Brevia — reporte de benchmark (datos sintéticos)

- Corpus: **64 prompts** sintéticos · semilla 42 (reproducible)
- Conteo de tokens: `heuristica char/4 (estimacion)`
- Bloques de código probados: **8** · violaciones de seguridad: **0**

## Resultado global

| Modo | Tokens totales | Ahorro total | Ahorro medio | Mediana |
|---|---|---|---|---|
| Seguro | 8,733 → 6,816 | 1,917 (22.0%) | 10.5% | 0.0% |
| Agresivo | 8,733 → 6,070 | 2,663 (30.5%) | 19.2% | 16.2% |

## Ahorro por categoría (modo seguro)

| Categoría | Tokens | Ahorro | % medio |
|---|---|---|---|
| duplicated_ctx | 2,479 → 1,534 | 945 | 36.6% |
| long_document | 3,083 → 2,111 | 972 | 29.2% |
| polite_verbose | 1,567 → 1,567 | 0 | 0.0% |
| code_heavy | 493 → 493 | 0 | 0.0% |
| already_tight | 148 → 148 | 0 | 0.0% |
| multilingual | 892 → 892 | 0 | 0.0% |
| chat_short | 71 → 71 | 0 | 0.0% |

## De dónde viene el ahorro (suma de tokens por paso)

**Modo seguro:**
- `dedup_parrafos` → 1,917 tokens
- `normalizar_espacios` → 0 tokens
- `recortar_lineas` → 0 tokens

**Pasos extra del modo agresivo:**
- `quitar_relleno` → 743 tokens
- `reducir_decoracion` → 0 tokens

## Chequeos de calidad

- **Seguridad de código:** ✅ todos los bloques de código intactos
- **Ahorro falso (already_tight):** máx 0.0% en prompts ya óptimos ✅ (bajo, no inflamos)

## Lectura honesta

El ahorro grande se concentra en `duplicated_ctx` y `long_document` (no reenviar lo mismo) — confirma que el valor real está en lo **estructural**, no en recortar palabras. Los prompts ya óptimos (`already_tight`) casi no cambian, que es lo correcto: la herramienta no debe inventar ahorro.
