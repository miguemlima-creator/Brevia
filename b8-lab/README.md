# B8 Lab — Escalón 0

Laboratorio para desarrollar **B8**: el "idioma emergente" de Miguel — un codebook
que se aprende de la interacción real del chat y vuelve denso lo que más se repite.
Esto es el **Escalón 0** del plan de escalado: evidencia barata, sin entrenar nada,
para saber si la idea tiene piernas antes de pedir recursos.

> Brevia = aporte al curso. **B8 = el proyecto propio.** Esto es su primera evidencia.

## La pregunta que hace o rompe la idea

Si construimos un codebook (frase frecuente → código corto) observando el chat,
¿ahorra tokens **netos**, es decir, *incluyendo* el costo de comunicarle el codebook
al modelo? Es el "BPE de nivel superior": en vez de fusionar caracteres frecuentes
(como el tokenizador), fusionar **frases/conceptos** frecuentes.

## Cómo correrlo

```bash
python b8-lab/experiment.py
```
Lee `corpus/*.txt`, construye el codebook, mide la economía y escribe `report.md`.

Para usar **tus chats reales** (tu ventaja injusta): exporta conversaciones a `.txt`
y déjalas en `corpus/`. El experimento las toma automáticamente.

## Qué encontramos (primer corrida, honesto)

- El codebook **sí ahorra neto** en régimen amortizado: **+8.8% en una sola pasada**,
  subiendo hacia **~27%** a medida que la conversación crece (el codebook es costo
  fijo; el ahorro escala con el volumen). Punto de equilibrio: **<1x** — se paga casi
  de inmediato.
- En régimen **per-message** (codebook en cada mensaje) **no compensa** — la idea solo
  vive si el codebook se **cachea y reusa**, nunca si se reenvía cada vez.
- Decode determinista **sin pérdida**.

**Lectura:** la hipótesis económica de B8 se sostiene, con una condición clara
(cachear el codebook). No es magia — en una sola pasada el ahorro es modesto; el valor
está en la conversación larga y reutilizada.

## Lo que el lab NO prueba todavía (siguiente escalón)

- **Decode zero-shot:** ¿puede el modelo reconstruir el texto codificado SIN que le
  demos el glosario entero? Si sí, el codebook casi no necesita viajar → el ahorro neto
  se dispara. Es la prueba fuerte y necesita un LLM en el loop (lo tenemos: el MCP de
  Brevia, o el modelo mismo).
- **Datos reales** de Miguel en vez del corpus de muestra.
- **El diferenciador:** que cada entrada del codebook guarde también **el porqué**
  (fusión con Engram) — eso es lo que lo separa de LLMLingua y del paper "Focus" (2026).

## Archivos

| Archivo | Qué es |
|---|---|
| `codebook.py` | Motor: minar frases, construir codebook, encode/decode, análisis económico |
| `experiment.py` | Corre el Escalón 0 y escribe el reporte |
| `corpus/` | Chat de muestra (vocabulario recurrente real); aquí van tus chats reales |
| `report.md` | Resultado de la última corrida |
