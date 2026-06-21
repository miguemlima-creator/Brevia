# Brevia

**Comprime el texto antes de que llegue al LLM. Menos tokens, menos datos, menos energía.**
Model-agnostic (Claude, ChatGPT, Gemini…), corre local, sin telemetría.

Casa propia del proyecto de Miguel — independiente del repo de TradingView de Lewis Jackson.

## Qué hay aquí

| Carpeta | Qué es |
|---|---|
| `brevia/` | La herramienta: motor CLI, extensión de navegador, servidor MCP, proxy, compresor semántico, cápsulas, paquetes para compartir |
| `b8-lab/` | La investigación **B8**: ¿puede el modelo crear su propio lenguaje comprimido? (taquigrafía zero-shot + codebook sectorial) |
| `dossiers/` | Informes de investigación en PDF |

## Las 4 puertas de Brevia (cada una corre en un lugar)

| Dónde usas la IA | Pieza | Cómo |
|---|---|---|
| Chat web (claude.ai, ChatGPT) | 🧩 Extensión | `brevia/extension/` → cargar en el navegador |
| Claude Code / Desktop | 📟 MCP | `brevia/MCP_SETUP.md` |
| App / API (devs) | 🔌 Proxy | `brevia/PROXY_SETUP.md` |
| Terminal, rápido | ⌨️ CLI | `python brevia/compress.py --file x.txt` |

## Empezar
- **Paper (preliminar, EN):** [`paper/PAPER.md`](paper/PAPER.md) — *Brevia: Self-Decodable Shorthand for Model-Agnostic Prompt Compression*
- Probar sin instalar nada: abre `brevia/extension/demo.html`.
- Mapa del proyecto y próximos pasos: `b8-lab/BLUEPRINT.md`.

---

© 2026 **Miguel Marrero**. Publicado bajo licencia **MIT** — uso libre **con atribución**
(ver `LICENSE.txt`). Brevia y la investigación B8 son de su autoría; el historial de git
acredita la fecha y el origen.
