# Brevia: Self-Decodable Shorthand for Model-Agnostic Prompt Compression

**Miguel Marrero**
Independent researcher · Toma Management LLC
*Preliminary report (v0.1) — June 2026*

> *Tokens are the new oil — and we are burning them. This is a preliminary,
> reproducible report of an idea to use them better.*

---

## Abstract

Every interaction with a large language model (LLM) consumes tokens, which cost money,
bandwidth, and energy. We study whether an LLM can rewrite text into its **own dense
shorthand** that a *different*, independent LLM can reconstruct **with no shared glossary
and no fine-tuning** (zero-shot). Across two languages and two task domains, model-native
shorthand achieved a mean of **~52% compression** (range 42–62%, n=3) while an independent
model recovered the meaning with **~90–100% fidelity** when given only the shorthand. We
further propose a **two-layer design**: (1) emergent shorthand for general language, and
(2) a small, cacheable **sectorial codebook** for proper nouns and domain jargon — the
terms that do *not* survive zero-shot decoding (e.g., novel acronyms). A prototype recovered
**6/6 such terms losslessly** at a codebook cost of ~14 tokens. We contrast this with a
purely deterministic phrase codebook, which is **marginal on real, diverse chat text**
(~2–6% net). All experiments are small and exploratory; we release the code, prompts, and
protocol and **invite the open-source community to scale and falsify these results.**

---

## 1. Introduction

LLM usage is metered in tokens. As adoption grows, aggregate token cost becomes a primary
operating expense, and each token also carries a data-transmission and energy footprint.
Most prompt-compression work either (a) relies on a helper model to prune tokens
(LLMLingua), or (b) requires fine-tuning to learn compressed representations (gist tokens),
or (c) reduces context at the API/gateway layer.

We ask a different, simpler question:

> **Can the model write its own compressed language — and can another model read it cold?**

If yes, the compressed form does not need a glossary to travel with it, which is what makes
the savings *net* rather than nominal. This report documents preliminary, reproducible
evidence that the answer is often "yes," characterizes when it fails, and proposes a
two-layer design that covers the failure mode.

Our framing constraints, chosen deliberately:
- **Model-agnostic** — works across providers, not one vendor.
- **Local / privacy-first** — text never leaves the user's machine; only anonymous metrics.
- **No fine-tuning** — everything here runs zero-shot, on hosted models as black boxes.

---

## 2. Related Work

- **LLMLingua (Microsoft).** Uses a small LM to drop low-information tokens; up to ~20x
  compression. Requires a helper model at inference time; the compressed text is not a
  language a second model is *meant* to natively decode.
- **Gist tokens (Mu et al., 2023).** Learns to compress prompts into cacheable "gist"
  tokens; requires modifying attention masks / fine-tuning.
- **Latent reasoning, e.g. Coconut (2024).** Models reason in continuous latent states
  rather than words; powerful but lives in the weights (training required).
- **Active context compression / "Focus" (2026).** An agent consolidates learnings into a
  persistent knowledge block and prunes raw history — adjacent to our "personal codebook"
  idea, at the agent-memory layer.
- **Format converters (e.g., MarkItDown).** Convert files to Markdown for LLMs; they do
  *not* compress — they are an ingestion stage upstream of this work.

**Positioning.** Unlike the above, we study *emergent, self-decodable* shorthand that an
LLM produces and a **different** LLM decodes **zero-shot, without any glossary or
training**, plus a complementary deterministic codebook for the terms that zero-shot
decoding cannot recover. We optimize for actual tokens sent (and bytes/energy), not just
per-token cost.

---

## 3. Method

### 3.1 Baseline: deterministic phrase codebook
Mine frequent multi-word phrases from a corpus, replace each with a short code (e.g. `§1`),
and ship a glossary. Lossless and exact, but the glossary must travel or be cached, so net
savings depend on reuse.

### 3.2 Model-native shorthand (the core idea)
Prompt the source model to rewrite a passage into the densest shorthand it believes another
AI could reconstruct **without a glossary** (abbreviations, symbols, arrows, fusions). The
shorthand is then handed to an **independent** model instance, with no original text and no
key, which is asked to reconstruct the full meaning.

### 3.3 Two-layer design (shorthand + sectorial codebook)
Zero-shot shorthand reliably preserves *known* terms (real place names, standard acronyms
like ROI/SWOT) but can lose **novel proper nouns/acronyms** that carry no shared meaning
(e.g., an invented project name). We therefore add a second layer: detect such "hard terms"
and bind them in a tiny, cacheable **sectorial codebook** (term → code), recovered
deterministically. The shorthand handles general language (lossy, ~50%); the codebook
guarantees the hard terms (lossless, small).

---

## 4. Experimental setup

- **Data collection.** A copy-paste "collector" prompt asks a hosted model (ChatGPT,
  Gemini) to emit a JSON packet with a representative ~100-token message, its shorthand,
  token estimates, and a compression estimate. A **privacy-preserving variant** returns
  only numbers and generic connectors (no verbatim text) for third-party participants.
- **Blind-decode protocol.** Each shorthand is passed to a fresh, independent model agent
  with no access to the original text, glossary, or prior context. Fidelity is graded by
  recovery of the original meaning-points.
- **Metrics.** Compression % (1 − shorthand/original tokens); blind-decode fidelity
  (fraction of meaning-points recovered). Token counts are estimates (≈4 chars/token) and,
  for self-reported packets, produced by the generating model.
- **Scale.** This is exploratory: **n = 3** real shorthand samples from 2 models / 3
  conversations, plus 4 blind-decode trials.

---

## 5. Results

### 5.1 Deterministic codebook is marginal on real text
On 64 synthetic prompts the codebook saved 22% (lossless) / 30.5% (aggressive), but those
prompts were seeded with repetition. On a single **real** chat, net amortized savings were
only **~2.4%**: real, diverse conversation has little exact repetition, and the glossary
cost dominates. **Conclusion: the deterministic codebook alone is not the win.**

### 5.2 Model-native shorthand compresses ~52%, decodes blind ~95%

| Source | Compression | Blind-decode fidelity |
|---|---|---|
| ChatGPT (user A) | 52% | ~90% (lost one novel acronym) |
| Gemini (user A) | 42% | ~100% |
| ChatGPT (user B) | 62% | ~100% |
| **Mean (n=3)** | **~52%** | **~95%** |

In every case an independent model reconstructed the meaning from shorthand alone — across
**English and Spanish**, and across **document editing, business planning, and meta
requests** — with **no glossary**. Encoders spontaneously used standard domain acronyms
(SWOT/FODA, ROI, CAPEX) as a *natural shared codebook* both models already understand.

### 5.3 The failure mode, and the two-layer fix
The single fidelity loss was a **novel acronym** ("B8") that the decoder could not guess —
exactly the case the sectorial codebook targets. A prototype detected hard terms
(acronyms, names, quoted terms) and recovered **6/6 losslessly** at a codebook cost of
~14 tokens (cacheable once). Shorthand + codebook together cover both general language and
hard terms.

---

## 6. Limitations (read this)

- **Tiny sample.** n=3 shorthand samples and 4 blind-decode trials. These are existence
  proofs, not statistics. The central claim ("~52%, ~95%") needs a real distribution.
- **Self-reported compression.** Some token counts/compression were produced by the
  generating model, not independently measured; counts are char/4 estimates, not provider
  billing.
- **Fidelity is meaning-graded**, not exact-match; graders were strong models, which may
  flatter zero-shot decoding. Weaker decoders may recover less.
- **Single-author, exploratory.** No ablations, no held-out test set, no human eval at scale.
- **Net-savings caveat.** Real savings require the compressed form to be self-decodable
  (shorthand) or the codebook to be cached; per-message glossary shipping erases the gain.

---

## 7. Discussion: why it might matter

If model-native shorthand is robustly self-decodable, it enables a **personal, growing
compression layer**: a local codebook that learns a user's recurring language over time, so
that more of each interaction compresses as the system "gets to know" them — reducing tokens
(and data, and energy) progressively, without sending anything to a server. It is
**model-agnostic** (a pre-processing layer, not a vendor feature) and **privacy-first**
(local). The vendor-side cost features (prompt caching, executor/advisor tiering) optimize a
different axis (per-token cost, not tokens-sent), so this is complementary, not competing.

Beyond cost, the deeper motivation is **co-adaptation**. As a person and the system work
through ideas together, the shared codebook enriches: the model's effective language
converges toward the user's, less needs to be spelled out, and the interaction grows more
attuned — the tool becomes, in a practical sense, *more like the person using it*. Token
reduction is the measurable surface of this convergence; the underlying aim is a personal,
portable layer that makes human–model collaboration progressively more fluent and more
**yours**. The compression is how we measure it; the fusion is why it matters.

---

## 8. Call for collaboration (open-source)

This idea is bigger than one non-specialist can scale. We are releasing it so it does not
die. **We would value help with:**
1. **Scale the study** — many users, many models, a real compression/fidelity distribution
   with proper statistics and ablations.
2. **Robustness** — when does zero-shot decoding break? Weaker decoders, longer contexts,
   adversarial content, cross-vendor pairs.
3. **The personal codebook** — an online-learning local codebook that improves with use.
4. **The strong version** — whether a model can *internalize* such a shorthand in its
   weights (training), which is beyond our resources.

Code, prompts, the privacy-preserving collector, and the ingestion/scoring scripts are in
this repository. Contributions, replications, and refutations are all welcome.

---

## 9. Reproducibility
- `b8-lab/` — codebook engine, two-layer prototype (`two_layer.py`), synthetic benchmark.
- `b8-lab/study/` — collector prompts (rich + privacy-safe), ingestor, scoring.
- `brevia/` — the model-agnostic compression tool (CLI, browser extension, MCP, proxy).
- Token counts use a ≈4-chars/token estimate; install `tiktoken` for exact GPT-family counts.

## Acknowledgments
Conceived and directed by Miguel Marrero. Implementation, experimentation, and drafting were
done with substantial assistance from Claude (Anthropic), used as a coding and research tool.

## References (informal)
- Mu et al., *Learning to Compress Prompts with Gist Tokens*, NeurIPS 2023. arXiv:2304.08467
- *Training LLMs to Reason in a Continuous Latent Space* (Coconut), 2024. arXiv:2412.06769
- *LLMLingua: Compressing Prompts...*, Microsoft. https://llmlingua.com
- *Active Context Compression: Autonomous Memory Management in LLM Agents*, 2026. arXiv:2601.07190
- *Neural Machine Translation of Rare Words with Subword Units* (BPE), Sennrich et al., 2015. arXiv:1508.07909

---

*© 2026 Miguel Marrero. Shared for open research — attribution required. See `LICENSE.txt`.*
