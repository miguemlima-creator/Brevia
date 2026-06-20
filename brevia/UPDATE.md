# Update para Miguel — 19 jun 2026 (mientras estabas fuera)

Hola Miguel. Seguí el hilo de la investigación, no borré nada, guardé la demo en
artefactos, y avancé en cuatro frentes. Aquí el resumen rápido. (Lo de siempre:
todo está en `brevia/`.)

## 1. Lab local + datos sintéticos ✅
`brevia/lab/` — un laboratorio para medir el producto con datos reales, no anécdotas.
- **64 prompts sintéticos** que imitan cómo escribe la gente (cortés, contexto
  duplicado, código, ya-óptimo, documentos largos, multilingüe, chat corto).
  Reproducibles (semilla fija). Generador: `lab/gen_synthetic.py`.
- **Benchmark** (`lab/benchmark.py`) que mide ahorro agregado, por categoría, por
  paso, y hace dos chequeos de calidad. Reporte: `lab/benchmark_report.md`.

**El lab ya pagó su precio:** encontró un **bug real** — los pasos "seguros"
rompían la indentación del código. Lo arreglé (ahora el código se blinda en todo
el pipeline, Python y JS). Sin el lab, eso se va a producción sin que nos demos cuenta.

## 2. Números honestos (64 prompts)
| Modo | Ahorro total | Mediana | Código intacto | Ahorro falso |
|---|---|---|---|---|
| Seguro | **22.0%** | 10.5% | ✅ | 0.0% ✅ |
| Agresivo | **30.5%** | 19.2% | ✅ | 0.0% ✅ |

Lo importante: **el 100% del ahorro seguro viene del dedup.** Normalizar/recortar
aportan ~0 en texto real. El valor está en *no reenviar lo mismo* — eso confirma
que **B2 (cápsulas de contexto) es el siguiente salto grande**.

## 3. Tu pregunta de "dentro del LLM" — investigada a fondo ✅
`brevia/inside-llm/RESEARCH.md` (con fuentes y búsquedas reales).

**El hallazgo clave (importante):**
- **Custom GPT / Gem / Skill NO reducen los tokens de entrada facturados.** Sus
  instrucciones llegan *después* de que la plataforma tokeniza el mensaje. Lo que
  sí logran: acortar la salida, cambiar el comportamiento, y **distribución masiva**
  (cero instalación → llegan a la gente que no programa, tu objetivo).
- **El verdadero "dentro de la ingeniería" es el proxy/gateway** (entre la app y la
  API del modelo) y el **MCP** para Claude. Ahí sí se ahorran tokens de entrada de
  verdad, model-agnostic. Es un mercado real creciendo **~49.6% al año** (Kong ya
  lo hace). **Tu instinto comercial apuntó al lugar correcto.**

**Te dejé 3 prototipos listos para copiar/pegar** (tu idea de crear GPT/Gem/Skill):
- `inside-llm/claude-skill/SKILL.md`
- `inside-llm/custom-gpt-instructions.md`
- `inside-llm/gemini-gem-instructions.md`

Y salieron 2 hitos nuevos: **B6 (proxy/gateway)** = el núcleo comercial, y
**B7 (paquetes de entrega)** = los GPT/Gem/Skill como puerta de entrada.

## 4. Demo guardada en artefactos ✅
`brevia/artifacts/demo-v0.1_2026-06-19.html` — snapshot **autocontenido** (motor
incrustado), se abre con doble clic, funciona sin internet y congelado tal cual hoy.
Punto de retorno por si algo se rompe. No se borra nada.

---

## Mi recomendación para cuando vuelvas
La tormenta debería empezar en **Claude** porque es donde más control "dentro"
tenemos hoy:
1. **B5 · MCP** — Brevia como herramienta nativa de Claude (compress/savings).
2. **B2 · Cápsulas de contexto** — el ahorro estructural que el benchmark señala.
3. En paralelo, prototipar **B6 · Proxy** — lo que escala a cualquier LLM y mide
   dólares de verdad.

Dime por cuál arrancamos y sigo. Todo documentado en `brevia/PROGRESS.md`.
```
                                                  — Claude Code, tu asistente
```
