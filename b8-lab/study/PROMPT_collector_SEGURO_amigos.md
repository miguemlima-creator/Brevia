# B8 · Prompt colector SEGURO (para amigos — sin filtrar texto)

> Úsalo con **otras personas**. Saca solo números y patrones genéricos: **NUNCA** texto
> real, nombres, montos ni temas de sus chats. El otro prompt (con fragmento/taquigrafía)
> es SOLO para tus propios chats.

---

## EL PROMPT (copiar desde aquí) ⬇️

```
You are helping with a small, privacy-respecting research experiment on text compression.
Using your memory of THIS user's past chats, return ONLY anonymous numbers and generic
style patterns.

CRITICAL PRIVACY RULE: do NOT include any verbatim text, names, amounts, money figures,
specific topics, or quotes from the conversations. Nothing personal or identifying. If a
"recurring phrase" contains any personal/topic content, replace it with a generic
placeholder or drop it.

Return ONLY this JSON object (no prose, no markdown fences):
{
  "source": "chatgpt | claude | gemini | grok | deepseek | other",
  "alias": "anon",
  "n_messages": <approx number of messages you can draw on>,
  "tokens_typical_message": <approx tokens of a TYPICAL message from this user>,
  "compression_pct_estimate": <if a typical message were rewritten in dense shorthand, about what % shorter — integer>,
  "recurring_phrases": ["<10-20 GENERIC conversational connectors this user repeats, e.g. 'ok', 'ayúdame', 'resúmeme', 'dame una lista' — ONLY generic patterns, NO names, NO numbers, NO money, NO topics, NO personal content>"],
  "style_note": "<one neutral sentence about HOW they write (concise / verbose / uses lists / asks step-by-step) — with NO personal content>"
}

Rules: NO original_fragment. NO shorthand of real text. recurring_phrases must be generic
patterns only. Valid JSON; single quotes (') inside strings, never double; keys in English.
```

---

## Por qué es seguro
- **No hay `original_fragment` ni `shorthand`** → no viaja ni un trozo de su conversación.
- `recurring_phrases` = solo **conectores genéricos** ("ok", "ayúdame", "resúmeme"), con
  instrucción explícita de no incluir nada personal/temático.
- Solo viajan **números** (tamaño, % de ahorro) + un patrón de estilo neutro.

## Qué perdemos (y por qué está bien)
- Con amigos NO medimos la *fidelidad* del decode a ciegas (eso necesita texto real).
  Esa prueba se hace **solo con tus propios chats** (donde no hay problema de privacidad).
- De los amigos sacamos la **distribución de compresión** + el **idioma compartido**
  (los conectores genéricos), que es lo que necesitamos sin tocar su intimidad.
