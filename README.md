# Brevia

**Compress text before it reaches the LLM. Fewer tokens, less data, less energy.**

Model-agnostic (Claude, ChatGPT, Gemini, local models). Runs locally. No telemetry.

> Tokens are the new oil — and we're burning them. Brevia trims the prompt
> *before* it ever hits the model, without changing what you're actually asking.

---

## Why

Every redundant paragraph, every "could you please kindly" is tokens — which means
money, bandwidth, and energy spent for nothing. Brevia cleans the text while
preserving your intent, then reports exactly how much you saved.

```
tokens   :     355  ->      229   (35.5% less)
bytes    :   1,528  ->      979   (bandwidth saved)
cost/call:  $0.000378  ->  ...
```

## The four doors (each runs where you already work)

| Where you use AI | Piece | How |
|---|---|---|
| Web chat (claude.ai, ChatGPT) | 🧩 Extension | load `brevia/extension/` in your browser |
| Claude Code / Desktop | 🖥️ MCP server | see `brevia/MCP_SETUP.md` |
| App / API (developers) | 🔌 Proxy | see `brevia/PROXY_SETUP.md` |
| Terminal, quick | ⌨️ CLI | `python brevia/compress.py --file x.txt` |

## Quick start (CLI)

```bash
# safe mode (lossless) — default
python brevia/compress.py --file prompt.txt --diff

# aggressive mode (also strips filler/politeness) — opt-in
python brevia/compress.py --file prompt.txt --aggressive --diff

# direct text, or pipe from stdin
python brevia/compress.py --text "Could you please help me with..."
cat prompt.txt | python brevia/compress.py
```

For exact token counts: `pip install tiktoken` (otherwise it estimates char/4).

## What it does

**Safe (default, lossless):** removes exact duplicate paragraphs, normalizes
whitespace and blank lines.

**Aggressive (`--aggressive`, opt-in):** removes filler/politeness that doesn't
change the instruction (bilingual EN/ES), reduces decoration (`---` rules, emoji
chains). **Never** touches code blocks and never changes your meaning.

**Shorthand (B8, opt-in):** the two-layer architecture from our research
(see `paper/PAPER.md`): the *model itself* rewrites your text in its own dense
shorthand (~50% compression, ~95% blind-decode fidelity, zero-shot), while a
persistent **personal codebook** shields hard terms (acronyms, proper nouns)
as stable `@n` codes so they survive losslessly. The codebook lives locally
(`~/.brevia/codebook.json`) and grows with use — the more you use it, the more
it speaks *your* language.

```bash
python brevia/shorthand.py pack --text "..."    # shield terms + LLM instruction
python brevia/shorthand.py unpack --text "..."  # restore @n codes
python brevia/shorthand.py book                 # your learned codebook
```

Inside Claude (MCP): `shorthand_pack` / `shorthand_expand` / `shorthand_book`.

## What's in this repo

| Folder | What it is |
|---|---|
| `brevia/` | The tool: CLI engine, browser extension, MCP server, proxy, semantic compressor, context capsules, B8 shorthand |
| `b8-lab/` | Research **B8**: can a model invent its own compressed shorthand? Validated (zero-shot stenography + sectorial codebook) — now shipped as `brevia/shorthand.py` |
| `paper/` | Paper render utilities (md → readable HTML) |

## Roadmap

- **Layer 1 — tokens:** lossless + aggressive compression (shipping, ~35–45%).
- **Layer 2 — voice:** a personal codebook that learns the *author's* writing style,
  so AI-assisted output still sounds like its owner. (v1 shipping: B8 shorthand —
  self-decodable model stenography + a personal codebook that grows with use)

## License

MIT — open with attribution. See `LICENSE`.
