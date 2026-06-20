# Blueprint — cómo seguimos

> Mapa para retomar sin perder el hilo. Lee esto primero al volver.
> (Resumen vivo del estado en `MEMORY.md` y `PROGRESS.md`.)

## Dónde estamos (20 jun 2026)

Dos cosas, separadas a propósito:

- **Brevia** = tu aporte al curso. **Completo y probado** (B1–B7: motor, extensión,
  MCP, proxy, semántico, paquetes). Listo para publicar cuando quieras.
- **B8** = tu proyecto propio. **Prueba de concepto PASADA hoy:** la taquigrafía nativa
  del modelo se auto-decodifica entre IAs, 2 idiomas, 2 dominios, sin glosario, ~47%
  compresión (4 mediciones independientes convergen ahí).

**Arquitectura de B8 validada:** dos capas que se completan —
1. **Taquigrafía** (zero-shot, gratis, no viaja): cubre el lenguaje general.
2. **Codebook sectorial** (mínimo, se cachea): cubre nombres propios + jerga de dominio
   (lo único que la taquigrafía no pudo sola — ej. "B8").

## El camino (escalera, con lo hecho marcado)

- [x] **E0** · Evidencia barata: codebook determinista (flojo en real, ~2-6%).
- [x] **E0.5** · Taquigrafía zero-shot (~47%, decode a ciegas funciona). ← *gran hallazgo*
- [x] **Loop de datos** · prompt colector + ingestor + 2 puntos reales.
- [ ] **E1 · Distribución** — juntar 10-20 taquigrafías (varios chats, varios modelos)
      → media y varianza de fidelidad + compresión. Convierte n=2 en evidencia seria.
- [x] **E2 · Prototipo "2 capas"** (`two_layer.py`) — taquigrafía + codebook sectorial.
      Probado: 6/6 términos duros (B8, SPY, LLC, Mrs Lima, Cuba…) recuperados sin pérdida,
      codebook 14 tok cacheable. La arquitectura completa de B8 funciona. Ver
      `E2-two-layer-results.md`. Falta: ahorro neto combinado real sobre datos de E1.
- [ ] **E3 · Narrativa** — Plan de B8 en PDF (con los números de E1/E2 adentro) +
      repo público + post. Lo que abre puertas a colaboradores/becas.
- [ ] **E4 · Ayuda y recursos** — 1 colaborador técnico, créditos de cómputo (Colab/
      Kaggle gratis → Google for Startups / AWS Activate), micro-becas (Emergent Ventures).
- [ ] **E5 · Lab mínimo** — tú + 1 colaborador + cómputo + cadencia. El último escalón.

## Decisiones que te tocan a ti

1. **¿Publicar Brevia ya** (cosechar el curso) o esperar?
2. **B8: ¿seguimos E1** (más datos) **o saltamos a E2** (prototipo 2 capas)?
   - Mi voto: **E1 primero** — barato, y la distribución hace creíble todo lo demás.
3. **¿El diferenciador es B8 + Engram** (compresión con memoria del *porqué*)? Eso es lo
   que nadie está juntando y sería tu foso.

## Recordatorio honesto

Es prueba de concepto, no producto. n pequeño, decoders fuertes. Y lo más importante:
**constrúyelo AL LADO de lo que te da de comer, no encima.** Sin apuro. La idea ya
demostró que respira; ahora es cuestión de alimentarla despacio.

## Lo primero al volver
1. Lee este blueprint + `b8-lab/study/decode_ciego_resultados.md`.
2. Decide: ¿E1 (más taquigrafías) o publicar Brevia?
3. Me dices y arrancamos.
