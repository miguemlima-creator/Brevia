# Brevia · "Dentro del LLM"

Investigación y prototipos para la idea de Miguel: que Brevia actúe **dentro** de
la ingeniería del LLM, no solo desde fuera.

## Archivos

| Archivo | Qué es |
|---|---|
| [RESEARCH.md](RESEARCH.md) | El análisis completo: fuera vs dentro, verdad sobre GPT/Gem/Skill, dónde está el ahorro real (proxy/MCP), arquitectura recomendada, fuentes |
| [claude-skill/SKILL.md](claude-skill/SKILL.md) | Skill de Claude (instrucciones de modo eficiente) — listo para instalar |
| [custom-gpt-instructions.md](custom-gpt-instructions.md) | Instrucciones listas para pegar en un Custom GPT de OpenAI |
| [gemini-gem-instructions.md](gemini-gem-instructions.md) | Instrucciones listas para pegar en un Gem de Google |
| [PUBLISH.md](PUBLISH.md) | Guía paso a paso para publicar los 4 paquetes (la acción la das tú) |
| [share-post.md](share-post.md) | Post listo para el Discord del team Claude (voz de Claude Code) |

## TL;DR del hallazgo

- **GPT / Gem / Skill** = distribución + comportamiento + salida más corta.
  **NO** reducen los tokens de *entrada* facturados (las instrucciones llegan
  después de que la plataforma tokeniza el mensaje). Hazlos igual: son el canal a
  la masa no técnica.
- **Proxy/Gateway + MCP** = el ahorro de tokens de entrada **real**, dentro del
  pipeline, model-agnostic. Es la dirección comercial seria (mercado +49.6%/año).
- Plan: empezar la tormenta en Claude (Skill + MCP, máximo control "dentro" hoy) y
  en paralelo prototipar el proxy que escala a cualquier LLM.

Nuevos hitos derivados: **B6 (proxy/gateway)** y **B7 (paquetes de entrega)**.
