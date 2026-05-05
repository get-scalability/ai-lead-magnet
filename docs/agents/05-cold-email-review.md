# Agent 05 — Cold Email Copy Review

**Persona:** Sales Team (SDR / AE)
**Target:** 500 unique executions (shared pool with Meeting Prep)
**Build:** Week 4 (last — simplest tool, no external data dependency)
**Slug:** `cold-email-review`

---

## Input

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Outbound email | Paste area | Yes | Free text, no character limit |
| Your company domain | Text | Yes | Scraped via HTTP to understand your offer — makes the review context-aware |

---

## Processing

1. **HTTP scrape** of submitter's domain → extract company description, offer, ICP, positioning
2. **Copywriting framework** applied as scoring rubric (from `/skills/copywriting-analyzer` + `/skills/copywriting-refiner`):
   - 11 scoring dimensions
   - Performance killer penalties
   - Accuracy classification per claim
3. **Claude** generates the full rewrite applying every identified fix

**No external API calls.** Self-contained: domain scrape + Claude + local framework.

---

## Scoring Framework (11 Dimensions)

| # | Dimension | What it measures |
|---|-----------|-----------------|
| 1 | Authenticity & Human Voice | Natural tone, passes 15-sec read-aloud test |
| 2 | Pattern Breaking & Opening | 5–15 word opener, trigger/tension/insight, no flattery |
| 3 | Optimal Length & Structure | 75–100 words, 6–10 lines, no sentence > 20 words |
| 4 | Concrete Value & Impact | Specific pain, concrete outcome, active phrasing |
| 5 | Loss Aversion Framing | Risks avoided, cost of inaction, not gain-only |
| 6 | Hybrid CTA Structure | Value question + 15 min + two specific day/time options |
| 7 | Seniority Appropriateness | Right altitude for the role (C-suite / VP / Manager / IC) |
| 8 | Value Proposition Relevance | Trigger → capability alignment, differentiated |
| 9 | Safe Social Proof | "Companies like…" phrasing, no fabricated metrics |
| 10 | Factual Accuracy | Every claim traceable, no hallucinations |
| 11 | Strategic Question | Non-generic, reply-driving, curiosity-inducing |

**Target benchmark:** 8.5%+ reply rate

### Performance Killer Penalties (−3 each)
- Uses the word "click" anywhere
- ROI / % benefits without verified source
- "Checking in / following up" language
- 2+ exclamation points
- ALL CAPS words or excessive punctuation

### Quality Checks (from copywriting-refiner)
- ❌ Em dashes (—) anywhere
- ❌ Rhetorical questions as openers
- ❌ Generic flattery without specific observation
- ❌ Pompous jargon (leverage, synergies, cutting-edge, game-changer, etc.)
- ❌ Email body starting with "I"
- ❌ Meeting ask in first touch
- ❌ Over word limit (120 words for email 1)
- ❌ Subject line > 6 words or Title Case

---

## Loading UX (Typewriter Intel)

```
🔍 Analyzing getscalability.io...
   → B2B sales intelligence · outbound-focused
🔍 Evaluating email structure...
   → 134 words · 12 lines · opens with "I noticed"
🔍 Scoring 11 dimensions...
   → Pattern interrupt: weak · CTA: too pushy
⚡ Rewriting with improvements...
```

---

## Output (streaming → structured cards)

### Score Card
```
authenticity:               7/10
pattern_breaking:           4/10  ⚠️
optimal_length:             5/10  ⚠️
concrete_value_impact:      6/10
loss_aversion_framing:      3/10  ❌
hybrid_cta_structure:       4/10  ⚠️
seniority_appropriateness:  8/10
value_proposition_relevance: 7/10
safe_social_proof:          9/10
factual_accuracy:           8/10
strategic_question:         5/10  ⚠️
penalties:                  −3
overall:                    5.9/10
```

### Top 3–5 Transformation Priorities
Specific, ordered by impact on reply rate.

### Per-Dimension Feedback
For each ⚠️ or ❌ dimension:
- What's wrong (quoted from the email)
- Why it hurts performance
- Specific fix suggestion

### Rewritten Email
Full rewrite with every fix applied:
- Subject line (≤ 6 words, lowercase)
- Body (75–100 words)
- CTA (value question + 15 min + two specific day options)
- `{personalization_variables}` labeled and explained

### "Why This Version Works Better"
3 bullet points on the key changes and why they improve reply rate.

---

## Gate

- Email captured **before** agent runs (see global gate logic)
- Full output visible after email submission (score + all feedback + full rewrite — no blur)
- **3 runs per email per month** (prevents one person reviewing 30 emails for free)
- Returning users within limit: skip gate form

---

## CRM Fields (Scala CRM push)

```json
{
  "tool_used": "cold_email_review",
  "tool_input_summary": "domain: getscalability.io | email: 134 words",
  "company_domain": "getscalability.io",
  "email_word_count": 134,
  "overall_score": 5.9
}
```

---

## Error Handling

### Domain Unresolvable
```
❌ "We couldn't find a website at [domain].
    The review will proceed without offer context
    — or fix the URL and try again."
```
*(Unlike other tools, this is a soft error — the review can still run, just less context-aware)*

### Email Too Short (< 20 words)
```
⚠️ "Your email seems very short. Paste your full email
    including subject line for the best review."
```

---

## Cross-tool CTA (post-output)

- → "Now prepare your meeting with this company" [link to Meeting Prep]
