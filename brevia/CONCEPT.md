# Brevia — concepto

> Comprimir el texto **antes** de que llegue al modelo.
> Para cualquier LLM. Para cualquier usuario. Ahorra tokens **y** datos.

## Por qué existe

graphify y Engram sirven a developers (mapean código). Pero la mayoría de la
gente **solo usa el chat** — pagan el plan, no programan, y cada conversación
larga les cuesta porque el modelo reenvía el historial en cada turno.

Brevia ataca eso desde la capa más universal: el **texto que entra al modelo**.
Como es pre-procesamiento, no depende del modelo → sirve a Claude, GPT, Gemini,
local, lo que sea.

Doble ahorro, los dos importan:
- **$ tokens** — menos tokens facturados.
- **bytes / energía** — menos data viajando = menos ancho de banda = menos energía.
  Interacción consciente con las máquinas.

## La verdad sobre cuánto se ahorra (honestidad primero)

No todo el ahorro es igual. Hay dos tipos:

| Tipo | Técnica | Ahorro típico | Riesgo |
|---|---|---|---|
| **Estructural** (el grande) | no reenviar lo mismo: dedup, referencias, cápsulas de contexto | 30–95% | bajo (sin pérdida) |
| **Cosmético** (el chico) | recortar relleno/cortesía, normalizar espacios | 5–30% | medio (puede tocar tono) |

En la prueba real (un prompt con contexto pegado 2 veces): **35.5%** solo con
dedup+espacios (sin pérdida), **44.8%** añadiendo recorte de cortesía.
El 80% del ahorro vino del **dedup**, no del recorte. Esa es la lección.

Por eso Brevia **por defecto es sin pérdida**. Lo agresivo es opt-in.

## Dónde encaja en el mapa de optimización de tokens

```
CAPA 1 Inferencia   — territorio de Anthropic/OpenAI (no lo tocamos)
CAPA 2 Recuperación — RAG (LlamaIndex, etc.)
CAPA 3 Contexto     — graphify (código)  ·  BREVIA (texto/chat)   <- aquí
CAPA 4 Memoria      — Engram (el por qué)
```

graphify comprime *código*. Brevia comprime *texto/chat*. Hermanos en la Capa 3.

## Roadmap

- [x] **B1 · Motor + CLI** (`compress.py`) — dedup, normalización, recorte opt-in,
      conteo de tokens (tiktoken opcional), reporte de ahorro $ + bytes. **Hecho.**
- [ ] **B2 · Cápsulas de contexto** — guardar bloques reutilizables (un documento,
      instrucciones) y referenciarlos en vez de re-pegarlos. El ahorro estructural grande.
- [ ] **B3 · Extensión de navegador** — comprimir inline en claude.ai / chatgpt.com
      antes de enviar, con el contador de ahorro visible. Para el usuario de chat no técnico.
- [ ] **B4 · Compresión semántica opcional** — modelo pequeño (estilo LLMLingua) para
      recortar manteniendo significado, sin GPU si se puede (cuantizado/CPU).
- [ ] **B5 · Medidor de sesión** — "esta sesión: 12k tokens en vez de 80k". Vivo, no benchmark.

## Limitaciones conocidas (v0.1)

- El dedup que borra un párrafo duplicado puede dejar huérfana su línea de intro
  (ej. "Te lo pego otra vez:"). Sin pérdida de info, pero queda raro. Pulir en B2.
- Sin tiktoken el conteo es estimación (char/4), no la factura exacta. Instala
  `tiktoken` para exactitud GPT (y buen proxy Claude).
- El recorte de cortesía es conservador a propósito; no es un parafraseador.
