# Conector remoto — usar tus MCP locales desde el móvil

Convierte cualquier MCP local de tu PC (Brevia, TradingView, etc.) en un
**conector personalizado de claude.ai**, para darle órdenes a Claude desde el
iPhone y que él llame a las herramientas que corren en tu escritorio.

```
iPhone (app de Claude)  ->  claude.ai  ->  túnel Cloudflare  ->  tu PC (gateway HTTP -> MCP stdio)
```

## Requisitos (una sola vez)

1. **Node.js** — si no lo tienes: https://nodejs.org (LTS) o `winget install OpenJS.NodeJS.LTS`
2. **cloudflared** — `winget install Cloudflare.cloudflared`
3. **Python** — ya lo tienes (Brevia corre con él).

## Paso 1 — Levantar el gateway + túnel

En PowerShell, desde la raíz del repo:

```powershell
.\remote-connector\start-connector.ps1
```

Por defecto expone el MCP de Brevia (`brevia\mcp_server.py`). El script abre
dos ventanas:

- **Gateway**: envuelve el MCP stdio en HTTP (puerto 8100, ruta `/mcp`).
- **Túnel**: cloudflared imprime una URL pública tipo
  `https://xxxx-yyyy.trycloudflare.com` — **cópiala**.

Para exponer otro MCP (ej. TradingView):

```powershell
.\remote-connector\start-connector.ps1 -McpCommand "python C:\ruta\a\tradingview_mcp.py" -Port 8101
```

## Paso 2 — Darlo de alta en claude.ai

1. En el navegador: **claude.ai → Configuración (Settings) → Conectores (Connectors)**
2. **Añadir conector personalizado (Add custom connector)**
3. URL: `https://<tu-url-del-tunel>.trycloudflare.com/mcp`
   - Si claude.ai rechaza la URL, prueba el modo SSE: relanza el script con
     `-Transport sse` y usa `https://<url>/sse`.
4. Guarda. (Los conectores personalizados están en los planes Pro/Max.)

## Paso 3 — Probar desde el iPhone

1. Abre la app de Claude → chat nuevo → activa el conector en el menú de
   herramientas del chat.
2. Dile: *"Usa brevia_savings y dime cuánto ahorra este texto: …"*
3. Si Claude responde con el ahorro, el circuito completo funciona:
   teléfono → nube → túnel → tu PC → de vuelta.

## Dejarlo permanente (opcional, recomendado)

- La URL de `trycloudflare.com` **cambia en cada arranque**. Para una URL fija
  crea un túnel con nombre (requiere dominio en Cloudflare, gratis):
  `cloudflared tunnel login`, `cloudflared tunnel create claude-pc`, y apunta
  un subdominio. Docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
- Para que arranque solo al encender la PC: Programador de tareas de Windows →
  nueva tarea al iniciar sesión → acción: `powershell -File <ruta>\start-connector.ps1`.
- Evita que la PC se suspenda: Configuración → Sistema → Energía → Suspender: Nunca.

## Seguridad

- La URL del túnel da acceso a las tools del MCP a **cualquiera que la tenga**.
  Con la URL efímera de trycloudflare el riesgo es bajo (nadie la conoce),
  pero para uso permanente protege el túnel con **Cloudflare Access** o usa
  un MCP que exija token.
- Expón solo MCP de **lectura/consulta** (reportar posiciones, comprimir
  texto). No expongas herramientas que muevan dinero o borren archivos.
