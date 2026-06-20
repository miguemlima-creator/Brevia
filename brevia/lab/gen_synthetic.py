# -*- coding: utf-8 -*-
"""
Brevia LAB · generador de datos sinteticos

Crea un corpus realista de prompts que imita como escribe la gente de verdad,
para medir el producto con datos en vez de anecdotas. Categorias:

  polite_verbose   — mucha cortesia/relleno (caso comun de usuario casual)
  duplicated_ctx   — pega el mismo contexto 2-3 veces (el ahorro estructural grande)
  code_heavy       — pregunta con bloques de codigo (probar que NO los rompemos)
  already_tight    — prompt ya optimo (probar que NO inventamos ahorro falso)
  long_document    — pega un documento largo + una pregunta corta
  multilingual      — mezcla ES/EN
  chat_short       — mensajes cortos tipo chat

Determinista (semilla fija) para que el benchmark sea reproducible.
Salida: brevia/lab/corpus/<categoria>_<n>.txt  +  manifest.json
"""
import json
import random
import re
from pathlib import Path

SEED = 42
random.seed(SEED)

OUT = Path(__file__).parent / "corpus"

# --- piezas reutilizables --- #
POLITE_OPEN = [
    "Hola, buenas, la verdad es que me gustaría que por favor me ayudaras con algo si no es mucha molestia. Muchas gracias de antemano.",
    "Hi, I was wondering if you could please help me with something. Thank you so much in advance.",
    "Buenas tardes, quisiera pedirte si fueras tan amable de ayudarme con una duda, te lo agradecería mucho.",
    "Hello, just wanted to ask, would you kindly help me out here? Thanks a lot.",
    "Oye, la neta, me gustaría que por favor revisaras esto cuando puedas, gracias de verdad.",
]
POLITE_CLOSE = [
    "Muchas gracias, de verdad te lo agradezco muchísimo. Saludos.",
    "Thank you so much, I really appreciate it. Best regards.",
    "Gracias de antemano, un abrazo.",
    "Thanks in advance, you're the best!",
    "De verdad mil gracias por tu tiempo y tu ayuda.",
]
TASKS = [
    "analiza este texto y dame la idea principal y un resumen corto",
    "summarize the following and list the key takeaways",
    "explícame qué significa esto en palabras simples",
    "review this and tell me if there are any problems",
    "tradúceme esto al inglés manteniendo el tono",
    "extrae los puntos accionables de lo siguiente",
]

PARAGRAPHS = [
    "La inteligencia artificial está transformando la economía global. Los modelos de lenguaje grandes consumen una unidad de cómputo llamada token. Cada interacción tiene un costo en tokens, tanto de entrada como de salida. Optimizar su uso no es solo ahorrar dinero, también reduce el tráfico de datos y el consumo de energía.",
    "Large language models are priced per token. As adoption grows, the aggregate cost of tokens becomes a major operating expense for any company building on top of these systems. Reducing context size directly reduces both cost and bandwidth.",
    "El cambio climático y el consumo energético de los centros de datos están ligados. Cada byte transmitido y procesado tiene una huella. Por eso la eficiencia en el uso de modelos no es solo económica, es ambiental.",
    "A well structured prompt gives the model exactly what it needs and nothing more. Redundant context, repeated documents, and verbose politeness all inflate the token count without improving the answer quality.",
    "El petróleo bajó en importancia relativa mientras subían nuevas formas de valor. Algunos piensan que los tokens de cómputo serán una unidad central de la economía digital del futuro, y que la eficiencia en su uso será una ventaja competitiva real.",
]

CODE_SNIPPETS = [
    "```python\ndef compress(text):\n    text = re.sub(r'[ \\t]+', ' ', text)\n    return text.strip()\n```",
    "```js\nfunction countTokens(s){\n  const chars = s.length;\n  return Math.round(chars/4);\n}\n```",
    "```sql\nSELECT user_id, SUM(tokens) AS total\nFROM usage\nGROUP BY user_id\nORDER BY total DESC;\n```",
]

TIGHT = [
    "Resume en 3 puntos: el costo de tokens sube con la adopción de IA y conviene optimizarlo.",
    "Translate to French: Tokens are the new oil.",
    "Fix this regex: ^\\d{3}-\\d{4}$ should allow optional country code.",
    "List 5 ways to reduce LLM context size.",
    "Convierte 25 grados Celsius a Fahrenheit y muestra la fórmula.",
]

CHAT_SHORT = [
    "oye y eso como se hace?",
    "dame un ejemplo rapido",
    "y si no funciona que hago",
    "ok y el siguiente paso?",
    "explicamelo como si tuviera 5 años",
    "thanks! and what about edge cases",
]


def wrap_polite(core):
    return f"{random.choice(POLITE_OPEN)}\n\n{core}\n\n{random.choice(POLITE_CLOSE)}"


def gen_polite_verbose(n):
    task = random.choice(TASKS)
    p = random.choice(PARAGRAPHS)
    core = f"Quisiera saber si podrías {task}.\n\nAquí está el texto:\n\n{p}\n\nPor favor analízalo bien."
    return wrap_polite(core)


def gen_duplicated_ctx(n):
    p = random.choice(PARAGRAPHS)
    task = random.choice(TASKS)
    times = random.choice([2, 2, 3])
    body = f"Necesito que {task}.\n\nAquí está el documento:\n\n{p}"
    for _ in range(times - 1):
        body += f"\n\nTe lo pego otra vez por si acaso no te llegó completo:\n\n{p}"
    return wrap_polite(body)


def gen_code_heavy(n):
    snip = random.choice(CODE_SNIPPETS)
    task = random.choice([
        "explica qué hace este código y si tiene bugs",
        "optimize this code and explain the change",
        "añade manejo de errores a esto",
    ])
    pre = random.choice(POLITE_OPEN)
    return f"{pre}\n\n{task}:\n\n{snip}\n\nPor favor sé detallado. Gracias."


def gen_already_tight(n):
    return random.choice(TIGHT)


def gen_long_document(n):
    # documento largo = varios parrafos, a veces con uno repetido
    k = random.randint(4, 6)
    paras = [random.choice(PARAGRAPHS) for _ in range(k)]
    if random.random() < 0.5:
        paras.append(paras[0])  # un duplicado escondido
    doc = "\n\n".join(paras)
    task = random.choice(TASKS)
    return f"{random.choice(POLITE_OPEN)}\n\nTengo un documento largo y necesito que {task}:\n\n{doc}\n\n{random.choice(POLITE_CLOSE)}"


def gen_multilingual(n):
    p_es = random.choice([x for x in PARAGRAPHS if "La " in x or "El " in x])
    p_en = random.choice([x for x in PARAGRAPHS if x[0].isupper() and " the " in x.lower()])
    return (f"Hi, please help me / hola por favor ayúdame.\n\n"
            f"Context in Spanish:\n{p_es}\n\n"
            f"Same idea in English:\n{p_en}\n\n"
            f"{random.choice(TASKS)}. Thank you so much, muchas gracias.")


def gen_chat_short(n):
    msgs = random.sample(CHAT_SHORT, k=random.randint(1, 2))
    return "\n".join(msgs)


GENERATORS = {
    "polite_verbose": gen_polite_verbose,
    "duplicated_ctx": gen_duplicated_ctx,
    "code_heavy": gen_code_heavy,
    "already_tight": gen_already_tight,
    "long_document": gen_long_document,
    "multilingual": gen_multilingual,
    "chat_short": gen_chat_short,
}

# cuantos de cada categoria
COUNTS = {
    "polite_verbose": 12,
    "duplicated_ctx": 12,
    "code_heavy": 8,
    "already_tight": 10,
    "long_document": 8,
    "multilingual": 6,
    "chat_short": 8,
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # limpiar corpus anterior (solo .txt del corpus, nada mas)
    for old in OUT.glob("*.txt"):
        old.unlink()

    manifest = []
    for cat, count in COUNTS.items():
        gen = GENERATORS[cat]
        for i in range(1, count + 1):
            text = gen(i)
            fname = f"{cat}_{i:02d}.txt"
            (OUT / fname).write_text(text, encoding="utf-8")
            manifest.append({"file": fname, "category": cat, "chars": len(text)})

    (OUT / "manifest.json").write_text(
        json.dumps({"seed": SEED, "total": len(manifest), "items": manifest},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")

    print(f"Generados {len(manifest)} prompts sinteticos en {OUT}")
    by_cat = {}
    for m in manifest:
        by_cat[m["category"]] = by_cat.get(m["category"], 0) + 1
    for c, n in by_cat.items():
        print(f"  {c:18} {n}")


if __name__ == "__main__":
    main()
