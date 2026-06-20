# B8 · Estudio multi-usuario (privacy-first)

Probar la hipótesis de B8 con **datos reales y diversos** (lote de ~10 amigos) sin
tocar ni un dato personal. Diseño: "lleva el código al dato, no el dato a ti".

## Piezas

| Archivo | Para quién | Qué es |
|---|---|---|
| `participante.html` | tus amigos | Página de un archivo. Corre en su navegador, analiza sus chats **local**, devuelve solo números anónimos. Nada se sube. |
| `CONSENTIMIENTO.md` | tus amigos | Consentimiento + instrucciones claras (2 min). |
| `POST_discord.md` | tú | El post para invitar (versión larga y corta). |
| `agregador.py` | tú | Junta los .json recibidos → distribución + `REPORTE_ESTUDIO.md`. |
| `resultados/` | tú | Aquí guardas cada .json que te manden. |

## Flujo

1. Postea `POST_discord.md` en el team. A quien se apunte, mándale por DM
   `participante.html` + `CONSENTIMIENTO.md`.
2. Cada amigo lo corre y te manda su JSON de números (voluntario).
3. Guardas los .json en `resultados/` y corres `python agregador.py`.
4. Sale `REPORTE_ESTUDIO.md` con la distribución → esa es la evidencia para el Plan de B8.

## La promesa de privacidad (cúmplela siempre)

- Sus conversaciones **nunca salen de su navegador**. Tú solo recibes números.
- El JSON no contiene texto de sus chats — solo porcentajes, tamaños y un alias.
- Voluntario y reversible: pueden no participar o pedir que borres su JSON.

Esto no es solo ética — es el **diferenciador** de B8: privacy-first por diseño, algo
que los compresores comerciales no ofrecen.
