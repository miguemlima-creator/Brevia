# B8 · Prueba dura — decode a ciegas de taquigrafías reales

**Fecha:** 2026-06-20 · 2 taquigrafías reales (de los paquetes de ChatGPT y Gemini),
decodificadas por subagentes independientes que SOLO recibieron la taquigrafía (sin
original, sin glosario, sin contexto).

## Caso 1 — ChatGPT (inglés)
- **Compresión:** 105 → 50 tokens (52%)
- **Fidelidad a ciegas:** ~90% (9/10 ideas recuperadas)
- **Único fallo:** "B8" → el decoder adivinó "Big-Eight-style" (acrónimo nuevo sin
  señal decodable; lo marcó como incierto él mismo). Leve deriva: "repeated phrases"
  → "reuse phrasing".

## Caso 2 — Gemini (español, edición de imágenes, símbolos ∅ y ->)
- **Compresión:** 68 → 39 tokens (42%)
- **Fidelidad a ciegas:** ~100% (7/7 ideas)
- Recuperó el significado **a pesar de los typos del original** ("retoala
  digitalmenmte") y descifró los símbolos (∅=no, ->=entonces). Reconstrucción casi
  exacta.

## Veredicto

La taquigrafía nativa del modelo **se auto-decodifica entre instancias independientes**,
en 2 idiomas y 2 dominios, sin glosario — con ~47% de compresión (consistente con las
3 mediciones previas). Es la evidencia más fuerte de B8 hasta ahora.

## Límite real descubierto (importante)

Los **nombres propios / acrónimos nuevos** (ej. "B8") NO sobreviven el decode a ciegas —
no cargan señal. Solución: un **glosario mínimo de términos** (los nombres propios y
jerga de dominio), que es justamente el codebook **sectorial** que Miguel propuso. O sea:
la taquigrafía cubre el lenguaje general (gratis, zero-shot), y un codebook chiquito
cubre los términos del dominio. Los dos juntos = B8 completo.

## Honesto
- n=2 taquigrafías. Hace falta más para una distribución de fidelidad.
- Los decoders eran modelos fuertes; uno débil podría recuperar menos.
- La fidelidad se calificó por recuperación de ideas, no palabra por palabra.
