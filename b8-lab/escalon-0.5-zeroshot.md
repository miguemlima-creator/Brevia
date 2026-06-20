# B8 Lab — Escalón 0.5: decode zero-shot de taquigrafía nativa del modelo

**Fecha:** 2026-06-20

## La pregunta

El Escalón 0 mostró que un codebook de códigos **opacos** (`§1`, `§2`) apenas ahorra
neto, porque el glosario tiene que viajar. Pregunta del 0.5: ¿y si el modelo escribe
su **propia taquigrafía semántica** (no códigos opacos, sino abreviaturas sugerentes)?
¿Puede **otro** modelo, a ciegas, sin glosario, reconstruirla? Esa es la versión fuerte
de B8 — "que la cápsula la escriba el modelo en su propio idioma".

## Diseño (sin trampa)

- **Agente A (codificador):** recibió un pasaje real en español, lo comprimió en su
  taquigrafía más densa "que otro AI pueda entender". Sin legend.
- **Agente B (descodificador, ciego):** recibió **solo** la taquigrafía de A — sin el
  original, sin glosario, sin el contexto de nuestra conversación — y reconstruyó.
- Subagentes independientes → prueba limpia (B no tenía forma de "ya saber" el original).

## Pasaje original (145 tokens)
> Mira Claude, lo que quiero es que sigamos trabajando en el ahorro de tokens pero que
> de verdad sirva para el chat troncal, no solo para Code... [115 palabras, voz de Miguel]

## Taquigrafía de A (76 tokens)
> Obj: seguir↓tokens, p/chat troncal (NO solo Code). Razón: muchos pagan plan+no
> programan→sufren costo. ≠solo $; tb tráfico-datos+energía=interacción consciente
> c/máquinas. Pedido: sé crítico conmigo, tómate tiempo, NO adules. Si algo
> fuera-de-alcance→dime mínimo necesario p/lograrlo, pero solo si pasos firmes. NO
> borres nada→tener a dónde volver x si acaso.

## Reconstrucción de B (a ciegas)
Recuperó **los 7 puntos** del mensaje: ahorro de tokens, chat troncal vs Code, la gente
que paga y no programa, dinero + datos + energía = interacción consciente, sé crítico /
tómate tiempo / no adules, mínimo-para-alcanzar solo con pasos firmes, y no borres nada.

## Resultado

| Métrica | Valor |
|---|---|
| Ahorro | 145 → 76 tokens = **47.6%** |
| ¿Viajó el glosario? | **No** |
| Fidelidad a ciegas | 7/7 puntos (perdió el saludo "Mira Claude" y matices finos) |

**Conclusión:** la taquigrafía **nativa y semántica** del modelo es decodable zero-shot
y ahorra ~48% **neto** — muy por encima del codebook opaco del Escalón 0, justamente
porque no necesita glosario. Esta es la dirección correcta de B8.

## Honestidad / límites (n=1, ojo)

- **Es una sola muestra.** Necesita repetirse con muchos pasajes para una distribución
  confiable. Un dato no es una ley.
- **Es lossy en los bordes:** se perdió el saludo y matices. Para chat está bien; para
  contenido preciso (código, cifras, legal) sería arriesgado — habría que combinar con
  el modo sin-pérdida (dedup/cápsulas) para esas partes.
- **Costo de codificar:** generar la taquigrafía cuesta tokens. El ahorro neto real
  depende de quién comprime y cuándo (idealmente un modelo pequeño/local comprime el
  mensaje del usuario antes de enviarlo).
- **Depende del codificador:** un modelo débil podría producir taquigrafía menos
  decodable.

## Siguiente (Escalón 1)
- Repetir con 10-20 pasajes reales → distribución de ahorro y fidelidad.
- Probar taquigrafía **persistente** (un estilo estable entre sesiones) → el inicio del
  "idioma propio".
- Diferenciador: que la taquigrafía guarde también **el porqué** (fusión Engram).
