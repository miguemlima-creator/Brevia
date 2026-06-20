# Brevia Proxy / Gateway (B6)

El ahorro de tokens **real**, model-agnostic, dentro del pipeline. La app apunta su
`base_url` al proxy; el proxy comprime y reenvía al proveedor real con tu API key.

```
App / Agente  ──>  [ BREVIA PROXY ]  ──>  OpenAI / Anthropic / Google
                   comprime aquí
```

## Probar sin API key (dry-run)

```bash
python brevia/proxy.py --dry-run --aggressive --port 8801
```
Manda un request estilo OpenAI a `http://127.0.0.1:8801/v1/chat/completions` y te
devuelve el ahorro + el payload comprimido (no reenvía nada).

## Usar de verdad

```bash
python brevia/proxy.py --upstream https://api.openai.com --port 8800
```
Luego en tu código apunta el cliente al proxy:
```python
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:8800/v1", api_key="sk-...")
# tus requests pasan por Brevia y se comprimen antes de llegar a OpenAI
```
El proxy reenvía tu `Authorization` tal cual. La respuesta trae el header
`X-Brevia-Saved-Tokens`.

## Medidor vivo

```bash
curl http://127.0.0.1:8800/stats
# {"requests":12,"tokens_in":...,"saved":...,"pct":...}
```

## Flags

| Flag | Qué hace |
|---|---|
| `--aggressive` | También quita relleno/cortesía (sin pérdida de significado) |
| `--semantic` | Compresión LOSSY (resume frases). Sube el ahorro a 40-60% pero descarta info |
| `--keep 0.6` | Con `--semantic`: cuánto conservar (0.6 = quita 40%) |
| `--capsules` | Expande referencias `[[cap:NOMBRE]]` antes de reenviar (ahorra banda cliente→proxy) |
| `--cache` | Caché de respuestas exactas: una llamada repetida no se reenvía (ahorra 100%) |
| `--dry-run` | No reenvía: devuelve el ahorro y el payload comprimido |

## Estado (scaffold funcional, ya crecido)

- ✅ Comprime el `content` de cada mensaje · dedup sin pérdida + recorte opcional
- ✅ **Dedup a nivel conversación**: quita mensajes exactamente duplicados (bug común
  de agentes) y acredita su ahorro en el medidor
- ✅ **Modo semántico** (B4) opcional · **cápsulas** · **caché de respuestas exactas**
- ✅ No toca código · no toca mensajes multimodales · medidor `/stats` · dry-run
- ✅ Forward con passthrough de credenciales (`Authorization` / `x-api-key`)
- ⏳ Próximo: multi-proveedor (traducir formato OpenAI↔Anthropic↔Google), caché
  *semántico* (no solo exacto), dashboard web del medidor.

## Honestidad

Ya comprime, deduplica, resume (opcional), cachea y reenvía — no es maqueta. Lo que
falta es la traducción entre formatos de proveedores y un caché por similitud (no
solo exacto). El ahorro sin pérdida viene del dedup; el ahorro grande (semántico) es
opt-in y lossy por diseño.
