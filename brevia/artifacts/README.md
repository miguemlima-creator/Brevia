# Brevia · Artefactos (puntos de retorno)

Snapshots congelados y **autocontenidos**. Aquí no se borra nada — es a donde
volver si algo se rompe más adelante.

## Contenido

| Archivo | Qué es |
|---|---|
| `demo-v0.1_2026-06-19.html` | Demo funcional con el motor **incrustado**. Se abre con doble clic, funciona sin internet y sin depender del código del repo. Es la foto de Brevia v0.1 del 19 jun 2026. |

## Por qué autocontenido

La demo viva (`../extension/demo.html`) carga el motor desde `brevia-engine.js`. Si
ese motor cambia, la demo viva cambia con él — bien para desarrollar, mal para
"recordar cómo era". Por eso el artefacto tiene el motor **pegado adentro**: queda
congelado tal cual estaba hoy. Pase lo que pase con el código, este archivo sigue
mostrando v0.1 exactamente.

## Regla

- **No borrar** estos archivos.
- Cada hito importante = un snapshot nuevo con fecha (`demo-vX_YYYY-MM-DD.html`).
- Si una versión nueva rompe algo, abrir el snapshot anterior y comparar.
