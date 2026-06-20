# B8 Lab — Escalón 0: ¿un codebook aprendido del chat ahorra tokens netos?

**Hipótesis:** si observamos la interacción real y construimos un codebook (frase frecuente → código corto), ¿se ahorran tokens *incluyendo* el costo de comunicarle el codebook al modelo? Es el "BPE de nivel superior" de Miguel.

## Datos

- Corpus: **3 sesiones**, 40 mensajes, **792 tokens** (estimados)
- Codebook: **20 entradas**, cuesta **151 tokens** comunicarlo
- Decode determinista sin pérdida: **sí ✅**

## Resultado económico (lo que hace o rompe la idea)

| Métrica | Valor |
|---|---|
| Ahorro en el texto (bruto) | 221 tokens (27.9%) |
| **Neto amortizado** (codebook 1 vez, estilo caché) | **+70 tokens (+8.8%)** |
| Neto per-message (codebook en cada mensaje) | -5819 tokens |
| Punto de equilibrio | reusar el corpus **0.68x** |

## Curva de amortización

El codebook es un **costo fijo** (se comunica una vez); el ahorro crece con el volumen de la conversación. Por eso el net% sube hacia el ahorro de texto (techo) a medida que la charla se alarga:

| Volumen de conversación | Neto | Net % |
|---|---|---|
| ×1 | +70 tokens | +8.8% |
| ×2 | +291 tokens | +18.4% |
| ×5 | +954 tokens | +24.1% |
| ×10 | +2059 tokens | +26.0% |
| ×20 | +4269 tokens | +27.0% |

## Codebook aprendido (top entradas)

| Código | Frase | tokens |
|---|---|---|
| `§1` | revenge trading estamos trabajando en estabilizar la | 11 |
| `§2` | miguel investiga esto a fondo y prepárame | 10 |
| `§3` | alcance te doy el mínimo para alcanzarlo | 10 |
| `§5` | análisis honesto del scalp y el riesgo | 9 |
| `§6` | tómate tu tiempo y dime la verdad | 9 |
| `§4` | interacción consciente con las máquinas | 8 |
| `§8` | dentro de la ingeniería del llm | 8 |
| `§9` | el stop loss y el take profit | 8 |

## Lectura honesta

- En régimen **amortizado** (el codebook viaja una vez y se reusa, como el prompt caching), el codebook **SÍ ahorra neto: +8.8%**. Esa es la condición de viabilidad — y se cumple.
- En régimen **per-message** (codebook en cada mensaje) **no compensa** — confirma que la idea solo vive si el codebook se **cachea/reusa**, no si se reenvía cada vez.
- El punto de equilibrio (**0.68x**) dice cuántas veces hay que reusar el contexto para que el codebook se pague solo.
- El decode determinista es sin pérdida; el **decode zero-shot por el modelo** (sin darle el codebook entero) es la prueba fuerte y es el siguiente experimento — requiere un LLM en el loop (lo tenemos vía el MCP de Brevia).

## Siguiente paso (Escalón 0.5)

- Probar **decode zero-shot**: darle al modelo texto codificado SIN el glosario completo y ver si lo reconstruye. Si lo logra, el codebook ni siquiera necesita viajar entero → el ahorro neto sube muchísimo.
- Probar con **chats reales exportados** de Miguel (su ventaja injusta) en vez del corpus de muestra.
- Diferenciador: que cada entrada del codebook guarde también **el porqué** (fusión con Engram).