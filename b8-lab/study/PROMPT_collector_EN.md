# B8 · Data Collector Prompt (English — faster, model-agnostic)

Paste this into **any AI** (ChatGPT, Claude, Gemini, Grok, DeepSeek…) together with —
or right after— the conversation you want to analyze. It returns a **JSON packet** with
everything B8 needs. Then paste that JSON to me (Claude Code) and I accumulate it into our
dataset with `ingerir.py` (it understands both English and Spanish keys).

> Privacy: this packet DOES include a text fragment and its shorthand (we need them to
> test reconstruction). Use it with YOUR own chats. For friends, use `participante.html`
> which only sends numbers.

---

## THE PROMPT (copy from here) ⬇️

```
You are a data collector for a language-compression experiment (project B8). Analyze the
REAL conversation/messages in this chat (the things actually discussed) — NOT this
instruction block. If the only text present is this instruction itself (no real
conversation), respond with exactly: {"error":"No conversation to analyze - paste a real chat first."}

Otherwise return ONLY a valid JSON object — no prose before or after, no markdown fences —
with EXACTLY these keys:

{
  "source": "chatgpt | claude | gemini | grok | deepseek | other",
  "alias": "anon",
  "n_messages": <integer, approximate>,
  "tokens_original_approx": <integer: estimate tokens of the analyzed text, ~4 chars/token>,
  "recurring_phrases": ["<the 10-20 phrases or expressions that repeat MOST in the chat>"],
  "original_fragment": "<one representative fragment of ~120 words, verbatim>",
  "shorthand": "<rewrite THAT SAME fragment in the densest shorthand another AI could reconstruct WITHOUT any glossary: abbreviations, symbols, arrows, fusions; no legend>",
  "tokens_shorthand_approx": <integer: estimate tokens of the shorthand>,
  "compression_pct_estimate": <integer: (1 - shorthand/original) * 100>,
  "notes": "<your optional observation, or null>"
}

Strict rules:
- Output ONLY the JSON. No explanations, no code fences.
- CRITICAL — keep the JSON valid: do NOT use double-quote characters (") INSIDE any
  string value. If the text contains quotes, replace them with single quotes ('). Only
  the JSON structure itself uses double quotes.
- Do not fabricate; if a field does not apply, use null.
- The shorthand must be reconstructable by another AI WITHOUT being given a glossary.
- "original_fragment" and "shorthand" must be the SAME fragment.
- Keep the keys in English exactly as shown. The phrases/fragment may be in the chat's
  own language.
```

---

## The loop

1. Paste the prompt into the AI where your conversation lives → it returns the JSON.
2. Paste that JSON to me (Claude Code).
3. I run `python b8-lab/study/ingerir.py` → it appends to `dataset.jsonl` and refreshes
   `REPORTE_B8_DATOS.md` (distribution + the **shared language** that emerges when the same
   recurring phrases show up across different chats).

Tip: run it on several of your chats and across different models (Gemini, Grok, DeepSeek)
— comparing how each one compresses is itself useful data.
