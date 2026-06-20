# Brevia MCP — registrar dentro de Claude (B5)

El servidor `mcp_server.py` expone Brevia como herramientas nativas de Claude
(Code o Desktop). Stdlib pura — solo necesita Python. 7 tools:

| Tool | Qué hace |
|---|---|
| `brevia_compress` | Comprime texto (dedup + recorte opcional), devuelve texto + ahorro |
| `brevia_savings` | Solo mide el ahorro (no devuelve texto) |
| `capsule_save` | Guarda un bloque reutilizable como cápsula |
| `capsule_list` | Lista las cápsulas |
| `capsule_pack` | Reemplaza contenido conocido por `[[cap:NOMBRE]]` |
| `capsule_expand` | Expande `[[cap:NOMBRE]]` a su contenido |
| `capsule_suggest` | Sugiere qué encapsular |

## Registrar en Claude Code

Crea (o edita) `.mcp.json` en la raíz del proyecto:

```json
{
  "mcpServers": {
    "brevia": {
      "command": "python",
      "args": ["C:\\Users\\Miguel Marrero\\tradingview-mcp-jackson\\brevia\\mcp_server.py"]
    }
  }
}
```

Reinicia Claude Code. Deberías ver las 7 tools `brevia_*` / `capsule_*` disponibles.

## Registrar en Claude Desktop

Edita `claude_desktop_config.json` (Settings → Developer → Edit Config) y añade el
mismo bloque `mcpServers`. Reinicia la app.

## Probar a mano (sin Claude)

```bash
python brevia/mcp_server.py
```
Luego pega una línea JSON-RPC y Enter:
```json
{"jsonrpc":"2.0","id":1,"method":"tools/list"}
```

## Notas

- El almacén de cápsulas vive en `~/.brevia/capsules.json` (persistente entre sesiones).
- stdout solo lleva JSON-RPC; los logs van a stderr (no rompen el protocolo).
- En Windows, el server fuerza UTF-8 en los streams (MCP lo exige).
- Si instalas `tiktoken` (`pip install tiktoken`), el conteo pasa de estimación a exacto.
