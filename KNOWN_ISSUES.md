# Known Issues

A single tracked home for known defects and limitations. `PROGRESS.md` stays focused on
feature milestones; bugs live here.

Many of the items below were found and reported by **Sar**, who ran a thorough black-box
QA pass (with `tiktoken` installed) against the CLI and semantic modules. Thank you, Sar —
this is exactly the kind of review that makes the project better.

---

## Fixed (2026-06-25)

| # | Issue | File | Fix |
|---|---|---|---|
| 1 | Safe mode shows 0% on typical single-shot prompts, which surprises users | `compress.py` | Report now prints a hint when savings are 0% ("safe mode only removes duplicates/whitespace; try --aggressive") |
| 2 | Orphaned intro line left dangling after a duplicate block is removed ("...te lo pego otra vez:") | `compress.py` (`dedup_blocks`) | If a removed duplicate was preceded by a short lead-in line (ends in `:` or matches a connector), the lead-in is removed too |
| 3 | Heuristic token count has large, directional errors (emojis −75%, code −23%) | `compress.py` (`report`) | Prominent "estimate" banner when `tiktoken` is absent; recommends `pip install tiktoken` |
| 4 | **(High)** Extractive summarizer silently dropped high-stakes sentences (legal clauses, deadlines, root cause) | `semantic.py` | High-stakes sentences (legal/deadline/obligation/negation patterns) are now force-protected; dropped sentences are returned and shown so the user can verify; renamed honestly to **"extractive summarization"** |
| 5 | Aggressive mode produced grammatically broken output (lowercase fragments, lost register) | `compress.py` | Post-pass re-capitalizes the first letter of each sentence after filler removal |

---

## Remaining limitations (honest)

- **Safe-mode savings are concentrated**, not universal. The ~22% aggregate benchmark figure
  comes mostly from prompts with duplicated/long context. On a typical non-repetitive
  message, safe mode legitimately saves ~0%. Claim it as "up to ~X%, concentrated in
  prompts with repeated context."
- **Token counts are estimates without `tiktoken`.** The fallback heuristic is roughest on
  emoji-heavy and code-heavy text. Install `tiktoken` for accurate GPT-family counts.
- **High-stakes protection (Finding 4) is heuristic.** `HIGH_STAKES_RE` won't catch every
  critical sentence. The summarizer is LOSSY by design — always review the shown `dropped`
  list before using its output for anything important.
- **Aggressive mode can still alter register.** Re-capitalization fixes broken grammar, but
  removing "Please/Could you" can shift a polite request toward an imperative. Use safe mode
  when tone matters.
- **The browser extension (JS engine) does not yet include the orphan-line and
  re-capitalization fixes** — those are in the Python CLI (`compress.py`). Porting them to
  `brevia/extension/brevia-engine.js` is a follow-up.

---

## How to report a new issue
Open a GitHub Issue with: a one-line description, the file/function affected, a minimal
reproduction (input + command + output), and—if you have one—a suggested fix.
