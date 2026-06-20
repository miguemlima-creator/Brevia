# B8 · E2 — Prototipo de 2 capas (resultados)

**Fecha:** 2026-06-20 · `two_layer.py`

## La idea
El Escalón 0.5 mostró que la taquigrafía nativa se decodifica a ciegas (~47%) **pero
pierde los términos duros** (nombres propios, acrónimos nuevos — "B8" se adivinó mal).
E2 prueba la solución: una segunda capa, un **codebook sectorial mínimo** de esos
términos, cacheado y determinista.

```
Capa 1 · TAQUIGRAFÍA  → lenguaje general (LLM, ~47%, zero-shot, lossy)
Capa 2 · CODEBOOK SECTORIAL → términos duros (determinista, cacheado, SIN pérdida)
```

## Resultado (caso con términos de varios sectores)
- Términos duros detectados: **6** — `B8, SPY, LLC, Mrs Lima, Cuba, Hola Miguel`
- Codebook: **14 tokens** (se envía 1 vez, se cachea)
- Recuperación de términos: **6/6 sin pérdida** ✅
- Sectores que emergen solos: acrónimo/código (B8, SPY, LLC), nombre propio (Cuba,
  Miguel), cita/term ('Mrs Lima').

## Veredicto
La arquitectura de 2 capas **funciona**: lo que la taquigrafía sola perdía (los términos
duros) la capa 2 lo recupera exacto, a costo mínimo y cacheable. B8 = taquigrafía (LLM,
general) + codebook sectorial (determinista, términos). Las dos mitades de la idea de
Miguel, unidas y probadas.

## Honesto / límites
- La **capa 1 (taquigrafía)** aquí se simula con el compresor por reglas como *proxy* —
  la taquigrafía real la genera un LLM (medida aparte ~47%). E2 prueba y mide la **capa 2**
  (la nueva, determinista) y la integración.
- La **detección** de términos duros es heurística (afinada para alta precisión: capta
  acrónimos, citas y nombres reales; ignora mayúsculas de inicio de frase). Aún puede
  capturar de más (ej. "Hola Miguel" en vez de solo "Miguel"). Mejorable con NER real.
- Siguiente: medir el ahorro NETO combinado real (taquigrafía LLM + codebook) sobre los
  paquetes reales del estudio (E1).
