# B8 · Smart all-chats collector prompt (English)

Open a NEW chat in an AI that remembers you (ChatGPT with Memory / "reference chat
history" ON works best; also Gemini, Grok, DeepSeek, Claude). Paste this once. It asks
the AI to profile ALL your chats from its memory and return the metrics + a JSON packet.
Copy the JSON block back to Claude Code.

---

## THE PROMPT (copy from here) ⬇️

```
Hi! Quick collaborative ask. I'm helping run a small research experiment we call "B8",
together with a human (Miguel) and another AI assistant (Claude). We're studying whether
the way a person talks with an AI can be rewritten into a dense shorthand that a DIFFERENT
AI could reconstruct WITHOUT any glossary — to cut the tokens, cost and energy that
conversations burn.

Using EVERYTHING you remember about my past conversations with you (your memory and my
chat history) — not just this single message — please profile how I tend to write and how
compressible it is. If you genuinely have no access to my past chats, tell me and ask me
to paste a few; otherwise work from your memory of them.

Give me TWO things:

PART 1 — a short, human-readable summary so I can SEE it:
  • my 15-25 most repeated phrases / expressions across our chats
  • ONE typical message of mine (~100 words), then that SAME message compressed into your
    densest no-glossary shorthand (abbreviations, symbols, arrows, fusions)
  • estimated tokens before -> after and % saved
  • one line on how repetitive / compressible my style is

PART 2 — a JSON packet inside a ```json code block, with EXACTLY these keys:
{
  "source": "chatgpt | claude | gemini | grok | deepseek | other",
  "alias": "anon",
  "n_messages": <approx number of messages/chats you are drawing on, or null>,
  "tokens_original_approx": <integer: tokens of the typical message>,
  "recurring_phrases": ["<my 15-25 most repeated phrases across all my chats>"],
  "original_fragment": "<the typical ~100-word message of mine, verbatim>",
  "shorthand": "<that same message in your densest no-glossary shorthand>",
  "tokens_shorthand_approx": <integer>,
  "compression_pct_estimate": <integer>,
  "notes": "<any observation, or null>"
}

JSON rules (important): valid JSON only; do NOT use double-quote characters (") inside any
string value — use single quotes (') instead; keep the keys in English exactly as shown.

Thanks — this is exactly the data I need. 🙏
```

---

## Notes
- Works best where the AI can see your history (ChatGPT Memory / reference-chat-history
  ON). If a model has no memory, it will ask you to paste a few chats — that's fine.
- You get a readable summary + a ```json block. Copy the JSON block to Claude Code → it
  gets ingested and the shared-language report updates.
