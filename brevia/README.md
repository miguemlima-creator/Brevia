# Brevia

**Comprime tus prompts antes de mandarlos a cualquier LLM. Ahorra tokens y datos.**

Model-agnostic (Claude, GPT, Gemini, local). Corre offline. Cero dependencias obligatorias.

## Para el usuario de chat (no técnico)

Pegaste un documento dos veces? Escribes con mucha cortesía? Eso son tokens
(= dinero + datos) de más. Brevia limpia el texto sin cambiar lo que pides.

```bash
# pega tu prompt en un archivo y:
python compress.py --file mi_prompt.txt --diff
# copia el "texto comprimido" y pégalo en el chat
```

## Uso rápido

```bash
# modo seguro (sin pérdida de significado) — default
python compress.py --file prompt.txt

# modo agresivo (además quita relleno/cortesía) — opt-in
python compress.py --file prompt.txt --aggressive --diff

# texto directo
python compress.py --text "Hola, por favor podrías ayudarme con..."

# guardar el resultado
python compress.py --file prompt.txt --out comprimido.txt

# salida JSON (para integrar en otra herramienta)
python compress.py --file prompt.txt --json

# desde stdin (pipe)
cat prompt.txt | python compress.py
```

## Qué hace

**Seguro (default, sin pérdida):**
- Quita párrafos duplicados exactos (pegar el mismo contexto 2 veces)
- Normaliza espacios y líneas en blanco de sobra

**Agresivo (`--aggressive`, opt-in):**
- Quita relleno/cortesía que no cambia la instrucción (bilingüe ES/EN)
- Reduce decoración (líneas `---`, cadenas de emojis)
- **No** toca código (` ``` ` o `` ` ``) ni cambia tu significado

## El reporte

```
tokens   :     355  ->      229   (+126 | 35.5% menos)
bytes    :   1,528  ->      979   (+549 B menos)     <- ancho de banda
por envio        : $0.000378
x 1,000 envios  : $0.3780
```

## Exactitud del conteo

Sin `tiktoken` usa una estimación (char/4). Para el conteo exacto:
```bash
pip install tiktoken
```

## Estado

v0.1 — motor + CLI funcionando. Ver `CONCEPT.md` para el roadmap (cápsulas de
contexto, extensión de navegador, medidor de sesión).
