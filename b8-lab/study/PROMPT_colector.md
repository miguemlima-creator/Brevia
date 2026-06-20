# B8 · Prompt colector de datos

Pega este prompt en **cualquier IA** (ChatGPT, Claude, Gemini…), junto con —o después
de— la conversación que quieras analizar. La IA te devuelve un **paquete JSON** con todo
lo que B8 necesita. Luego me pegas ese JSON a mí (Claude Code) y yo lo acumulo en
nuestro dataset con `ingerir.py`.

> Privacidad: este paquete SÍ incluye un fragmento de texto y su taquigrafía (lo
> necesitamos para probar la decodificación). Úsalo con TUS propios chats. Para amigos,
> usa el kit `participante.html` que solo manda números.

---

## EL PROMPT (copia desde aquí) ⬇️

```
Eres un colector de datos para un experimento de compresión de lenguaje (proyecto B8).
Analiza la CONVERSACIÓN real de este chat (lo que de verdad se conversó) — NO este bloque
de instrucciones. Si lo único presente es esta instrucción (sin conversación real),
responde exactamente: {"error":"No hay conversacion que analizar - pega un chat real primero."}

Si no, devuelve ÚNICAMENTE un bloque JSON válido, sin una sola palabra antes ni después,
con EXACTAMENTE este formato:

{
  "fuente": "chatgpt | claude | gemini | otro",
  "alias": "anon",
  "n_mensajes": <entero aproximado>,
  "tokens_original_aprox": <entero: estima tokens del texto analizado, ~4 chars/token>,
  "frases_recurrentes": ["<10 a 20 frases o expresiones que MÁS se repiten en el chat>"],
  "fragmento_original": "<un fragmento representativo de ~120 palabras, tal cual>",
  "taquigrafia": "<reescribe ESE MISMO fragmento en la taquigrafía MÁS densa posible que OTRA IA pueda reconstruir SIN glosario: abreviaturas, símbolos, flechas, fusiones; sin leyenda>",
  "tokens_taquigrafia_aprox": <entero: estima tokens de la taquigrafía>,
  "compresion_pct_estimada": <entero: (1 - taquigrafia/original) * 100>,
  "notas": "<observación tuya opcional, o null>"
}

Reglas estrictas:
- Responde SOLO el JSON. Nada de texto explicativo, ni ```.
- CRÍTICO — mantén el JSON válido: NO uses comillas dobles (") DENTRO de ningún valor de
  texto. Si el texto trae comillas, cámbialas por comillas simples ('). Solo la
  estructura del JSON usa comillas dobles.
- No inventes; si un campo no aplica, pon null.
- La taquigrafía debe poder reconstruirse por otra IA SIN que le des un glosario.
- El fragmento_original y la taquigrafia deben corresponder al MISMO fragmento.
```

---

## Cómo lo usamos (el loop)

1. Pegas el prompt en la IA donde está tu conversación → te devuelve el JSON.
2. Me pegas ese JSON aquí (a Claude Code).
3. Yo lo guardo con `python b8-lab/study/ingerir.py` → se acumula en `dataset.jsonl` y
   se actualiza `REPORTE_B8_DATOS.md` (distribución + el "idioma compartido" que emerge
   de juntar las frases recurrentes de todos).

Cada paquete es un punto de datos real. Mientras más juntemos, más fuerte la evidencia.
