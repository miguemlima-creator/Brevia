# Brevia — extensión de navegador (B3)

Comprime tus prompts **inline** en claude.ai, ChatGPT y Gemini. También trae un
popup que funciona en cualquier sitio. Todo 100% local, model-agnostic.

## Probar YA sin instalar nada

Abre **`demo.html`** con doble clic (se abre en tu navegador). Pega un prompt,
dale "Comprimir", mira el ahorro. Es la forma más rápida de enseñarlo en Big School.

## Instalar la extensión (Chrome / Edge / Brave)

1. Abre `chrome://extensions` (o `edge://extensions`)
2. Activa **"Modo de desarrollador"** (arriba a la derecha)
3. Click **"Cargar descomprimida"** / "Load unpacked"
4. Selecciona esta carpeta: `brevia/extension/`
5. Listo. Verás el icono de Brevia en la barra.

## Cómo se usa

**Inline (en el chat):** entra a claude.ai o chatgpt.com. Abajo a la derecha
aparece el botón **✦ Brevia**. Escribe tu prompt, click → "Comprimir lo que
escribí". El texto se reemplaza comprimido y sale un aviso con el ahorro.

**Popup (cualquier sitio):** click en el icono de Brevia → pega texto → Comprimir
→ Copiar. Útil para cualquier IA o app.

## Modos

- **Seguro** (default): sin pérdida de significado — quita duplicados y espacios.
- **Agresivo**: además quita relleno/cortesía. No toca código.

## Archivos

| Archivo | Qué es |
|---|---|
| `manifest.json` | Config MV3 |
| `brevia-engine.js` | Motor de compresión (puro, compartido) |
| `content.js` + `content.css` | Botón flotante inline en los chats |
| `popup.html` + `popup.js` | Compresor standalone (cualquier sitio) |
| `demo.html` | Demo abrible sin instalar |

## Notas honestas

- El reemplazo **inline** es best-effort: las webs cambian su DOM seguido. Si un
  día deja de reemplazar bien, el **popup** y el **demo** siempre funcionan.
- El conteo de tokens es estimación (el navegador no tiene tiktoken). El motor
  de la CLI (`../compress.py`) sí usa tiktoken si está instalado, para exactitud.
- Sin telemetría, sin red, sin cuentas. Tu texto no sale de tu máquina.
