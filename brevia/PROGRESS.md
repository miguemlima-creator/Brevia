# Brevia — progreso

Herramienta de Miguel + Claude. Capa 3 (contexto), hermana de graphify.
Wedge: **comprimir el texto antes del LLM** — model-agnostic, para chat y Code,
ahorra tokens **y** ancho de banda. Concepto completo: `CONCEPT.md`.

## Hitos

- [x] **B1 · Motor + CLI** (`compress.py`)
  Dedup de párrafos (sin pérdida), normalización de espacios, recorte de
  relleno/cortesía opt-in (bilingüe, no toca código), conteo de tokens
  (tiktoken opcional + fallback heurístico), reporte de ahorro $ + bytes + por paso.
  **Probado:** prompt con contexto duplicado → **35.5%** seguro / **44.8%** agresivo.
  El grueso del ahorro vino del **dedup**, no del recorte de palabras.

- [x] **B2 · Cápsulas de contexto** (`capsules.py`)
  Guardar bloques reutilizables (almacén `~/.brevia/capsules.json`) y `pack`/`expand`
  con referencias `[[cap:NOMBRE]]` + `suggest`. **Probado:** roundtrip sin pérdida,
  un prompt con doc duplicado pasó de 223 → 78 tokens (**−65%**). Marcador ASCII por
  robustez en Windows. El ahorro estructural grande, confirmado por el benchmark.
- [x] **B3 · Extensión de navegador** (`brevia/extension/`)
  Manifest V3 + motor JS portado (paridad con la CLI: 35.5% seguro), botón
  flotante inline en claude.ai/chatgpt/gemini (reemplazo vía execCommand para
  React/ProseMirror), popup standalone para cualquier sitio, y `demo.html`
  abrible sin instalar. **Hecho.** Ver `extension/README.md` para cargarla.
- [x] **LAB · datos sintéticos + benchmark** (`brevia/lab/`)
  Generador de 64 prompts sintéticos (7 categorías, semilla 42 reproducible) +
  harness que mide ahorro agregado, por categoría, por paso, y CHEQUEA seguridad
  de código + ahorro falso. **Hecho.** Encontró y arregló un bug real: los pasos
  seguros rompían la indentación del código → ahora se blinda el código en todo el
  pipeline (Python y JS). Resultado: **22.0% seguro / 30.5% agresivo** sobre 64
  prompts; 100% del ahorro seguro = `dedup`. Ver `lab/benchmark_report.md`.

- [x] **INSIDE-LLM · investigación** (`brevia/inside-llm/`)
  Respuesta a la idea de Miguel (dentro vs fuera del LLM). Hallazgo: GPT/Gem/Skill
  = distribución + comportamiento, NO ahorro de input; el ahorro real "dentro" =
  proxy/gateway + MCP. Prototipos listos: Claude Skill, Custom GPT, Gemini Gem.
  Ver `inside-llm/RESEARCH.md`. De aquí salen B6 y B7.

- [x] **B4 · Compresión semántica** (`semantic.py`) — extractiva estadística (TF +
  posición), LOSSY opt-in con ratio `--keep`, protege código/números/preguntas. Sin
  GPU, stdlib. **Probado:** documento largo 437 → 254 tokens (−41.9%), código intacto.
  Marcada claramente como lossy (resume, no es sin pérdida). Neural (LLMLingua real)
  queda como opción futura.
- [x] **B5 · Servidor MCP** (`mcp_server.py`) — stdlib pura (JSON-RPC sobre stdio),
  7 tools (`brevia_compress`, `brevia_savings`, `capsule_*`). **Probado:** handshake
  initialize/tools/list/tools/call OK, manejo de errores OK. Fuerza UTF-8 en Windows.
  Registro en `MCP_SETUP.md`. El "dentro" nativo de Claude.
- [x] **B6 · Proxy/Gateway** (`proxy.py`) — drop-in `base_url` estilo OpenAI, comprime
  el `content` de cada mensaje y reenvía con passthrough de credenciales; medidor vivo
  en `/stats`; modo `--dry-run`. **Probado:** 73 → 39 tokens (−46.6%) y meter acumula.
  stdlib pura (http.server + urllib). Setup en `PROXY_SETUP.md`. El ahorro de input
  REAL, model-agnostic. Núcleo comercial — scaffold listo para crecer.
- [x] **B7 · Paquetes de entrega** — los 4 paquetes listos para publicar (Claude Skill,
  Custom GPT, Gemini Gem, extensión) + guía paso a paso `inside-llm/PUBLISH.md` + post
  para el team `inside-llm/share-post.md`. La acción de "publicar" la da Miguel (cuentas).

- [x] **Proxy crecido** (`proxy.py`) — añadido: dedup a nivel conversación (acreditado
  en el medidor), modo semántico (`--semantic --keep`), expansión de cápsulas
  (`--capsules`), caché de respuestas exactas (`--cache`). Probado en dry-run.

- [x] **B8 · Shorthand de 2 capas** (`shorthand.py`) — **la fusión Brevia + B8**
  (2 jul 2026). La arquitectura validada en el lab (E0.5 + E2: taquigrafía
  zero-shot ~52% / ~95% fidelidad ciega + codebook sectorial) ahora es módulo de
  producto: codebook **persistente** en `~/.brevia/codebook.json` con códigos `@n`
  ESTABLES entre sesiones (lección E0: el codebook solo compensa cacheado) que
  crece con el uso — la semilla del "idioma personal" / B8 vivo. CLI
  (`pack`/`unpack`/`book`) + 3 tools MCP (`shorthand_pack/expand/book`, server
  v0.2.0, 10 tools). **Probado:** detección 6/6 términos duros de la muestra E2,
  códigos reutilizados entre procesos, roundtrip de restauración exacto, handshake
  MCP y las 10 tools OK. La capa 1 (taquigrafía) la escribe el LLM que llama.

## Correr B1 / LAB

```bash
python brevia/compress.py --file <prompt.txt> --diff
python brevia/compress.py --file <prompt.txt> --aggressive
python brevia/lab/gen_synthetic.py     # regenera el corpus
python brevia/lab/benchmark.py         # mide y escribe el reporte
```

## Pendientes / ruido conocido (pulir en B2)
- El dedup puede dejar huérfana la línea de intro de un párrafo borrado
  ("Te lo pego otra vez:"). Sin pérdida de info, pero queda raro.
- Sin tiktoken el conteo es estimación; instalar para exactitud.
