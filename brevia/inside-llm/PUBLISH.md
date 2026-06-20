# Brevia · Guía de publicación (B7)

Todo está listo para publicar. Estos pasos los das **tú** (necesitan tus cuentas).
Cada paquete tarda ~5 minutos.

---

## 1. Claude Skill

**Opción A — personal (tu máquina):**
1. Copia la carpeta `claude-skill/` a `~/.claude/skills/brevia/`
   (en Windows: `C:\Users\Miguel Marrero\.claude\skills\brevia\`).
2. Reinicia Claude Code. Se activa sola cuando pegas documentos largos o pides ahorrar.

**Opción B — compartir con el team:**
- Sube la carpeta `claude-skill/` a un repo o zip y que cada uno la copie a su
  `~/.claude/skills/`. (Es solo el `SKILL.md`.)

---

## 2. Custom GPT (OpenAI) — requiere ChatGPT Plus

1. Ve a https://chatgpt.com/gpts/editor
2. Pestaña **Configure**.
3. Copia el contenido de `custom-gpt-instructions.md`:
   - **Name** → "Brevia — Token Saver"
   - **Description** → la del archivo
   - **Instructions** → el bloque de código
   - **Conversation starters** → los 4 del archivo
4. (Opcional avanzado) Si despliegas el proxy como API pública, añade una **Action**
   apuntando a `/compress` para ahorro de entrada real.
5. **Create** → elige "Anyone with the link" → copia el link para el team.

---

## 3. Gemini Gem (Google) — requiere Gemini

1. Abre Gemini → **Gem manager** → **New Gem**.
2. Nombre: "Brevia — Ahorra Tokens".
3. Pega el bloque de instrucciones de `gemini-gem-instructions.md`.
4. Guarda. Compártelo si tu plan lo permite.

---

## 4. Extensión de navegador (la que ya hicimos, B3)

- Carpeta `../extension/`. Pasos en `../extension/README.md`.
- Para el team: zip de `extension/` + "Cargar descomprimida" en chrome://extensions.
- (Más adelante) publicar en la Chrome Web Store para instalación de un clic.

---

## 5. Proxy (para devs del team, B6)

- `../proxy.py`. Pasos en `../PROXY_SETUP.md`.
- El que use la API de OpenAI/Anthropic apunta su `base_url` al proxy y ahorra ya.

---

## Qué decir al compartir

Ver `share-post.md` en esta carpeta — un post listo para pegar en el Discord del
team Claude, en la voz de Claude Code presentándolo de parte de Miguel.

## Recordatorio honesto (dilo si preguntan)
- Skill/GPT/Gem = ahorro de **salida** + comportamiento + distribución. NO ahorro de
  entrada facturado.
- Extensión + Proxy = ahorro **real** de tokens/datos.
Los cuatro juntos cubren todo el espectro.
