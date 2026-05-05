# AI Lead Magnet Platform — Product Spec

**Version:** 2.0
**Date:** 2026-05-05
**Owner:** Yazid
**Status:** Ready to build

---

## 1. Overview

A public-facing platform of 5 AI-powered tools embedded as React widgets on `getscalability.io`. Each tool acts as a gated lead magnet targeting a specific persona (Sales / Growth / CMO–CRO). The platform captures inbound leads, pushes them to Scala CRM with full context, and generates qualified pipeline.

**Primary goal:** 500 unique executions on Sales + Growth tools, 50 ICP companies onboarded via CMO/CRO tools.

---

## 2. Architecture

### Frontend
- **React widgets** embedded via `<script>` tag on `getscalability.io` pages
- Each tool is a self-contained widget rendered in a `<div>` on a marketing page
- Deployment target: TBD (Webflow embed vs. Next.js subdomain `tools.getscalability.io`)
- **Copy: hardcoded EN/FR in components** (v1) — Notion CMS deferred to v2
- No authentication required — anonymous first, email gate before agent runs
- **Desktop-first for v1** — mobile optimization deferred to v2

### Backend
- **FastAPI** — `ai-lead-magnet` repo, simplified stack (no RabbitMQ, no worker, no scheduler)
- **5 AI agents** powered by Anthropic Claude directly via `anthropic` SDK (`ANTHROPIC_API_KEY`)
- **Streaming responses** via `sse-starlette` — direct token streaming from Claude to client. No LangGraph, no message queue. Pattern: `POST /agents/{slug}` → `anthropic.messages.stream()` → SSE response
- **Scala API** (`SCALA_APP_API_URL`) — single source for all company + contact intelligence (ICP scores, profiles, benchmarks, industry data)
- **PostgreSQL** — rate limiting, shareable link storage, lead run tracking (Alembic migrations)
- **Pinecone** — semantic search over indexed Lemlist campaign data (Best Campaigns agent only)
- **Gotenberg** — PDF export for Sales Business Plan

### Data sources (per tool)
| Tool | Sources |
|------|---------|
| Cold Email Review | Domain HTTP scrape + Claude + copywriting skills framework |
| Meeting Prep | Scala API + Claude |
| Company List | Scala API + Claude |
| Sales Business Plan | Domain HTTP scrape + Scala API + Claude |
| Best Campaigns | User domain scrape + target domain scrape + Scala API + Lemlist PostgreSQL + Pinecone + Claude |

**Linkup: not used.** All intelligence comes from Scala's own data stack.

### CRM
- All leads pushed to **Scala CRM** (`SCALA_CRM_API_URL`) with full context
- Rate limiting: **PostgreSQL table** `lead_magnet_run (email_hash, tool_slug, month, run_count)`
- No Redis needed

### Copywriting framework
1,724 lines of proprietary scoring framework (7 files). Copied into `app/skills/copywriting-*/` at build time and loaded as the system prompt for the Cold Email Review agent. Injected once with Anthropic prompt caching — reused across all runs at 10% input token cost.

---

## 3. Email Gate Logic

**Model: email first → agent runs → full output**

Email is captured **before** the agent runs. This ensures:
1. Lead is captured regardless of output quality
2. No wasted API calls on non-converting sessions

```
User submits input
    ↓
Email capture form shown immediately
    ↓
User submits email + optional first name
    ↓
Email + input pushed to Scala CRM (pre-run)
    ↓
Agent runs
    ↓
Loading UX shown (typewriter intel — see §7)
    ↓
Full output streamed and rendered
    ↓
Run counter incremented in PostgreSQL
```

**Form fields:**
- Email (required)
- First name (optional — label: "So we can personalize follow-ups")

**Email validation:** Any valid email accepted. CRM handles quality flagging.

**RGPD consent:** No checkbox. Below the submit button, small grey text:
> "By getting your results, you'll occasionally hear from Scalability. [Unsubscribe anytime] · [Privacy policy]"

This is implicit consent tied to value delivery — standard practice (HubSpot, Apollo, etc.), RGPD-compliant when opt-out is clearly accessible.

**Rate limit enforcement (PostgreSQL):**
- Default: **3 free runs per email per month** (all tools except Sales Plan)
- Sales Plan: **3 lifetime runs** per email
- Returning users within limit: skip gate form, go straight to agent
- On limit reached: "You've used your 3 free runs this month. Reset on [date]. [Book a demo →]"

---

## 4. Shareable Links

| Mode | URL | Use case |
|------|-----|---------|
| **Result permalink** | `/r/{uuid}` | Share read-only result with a colleague. Visitor sees full output + gate to run their own. |
| **Pre-filled tool link** | `/tools/meeting-prep?company=hubspot.com&ref=yazid` | Outbound use — "I prepared a briefing for your company." Visitor hits email gate, gets result. |

- Result stored in PostgreSQL: `uuid → output_json + tool + input + created_at`
- Results expire after 30 days
- Shareable links include UTM attribution

---

## 5. The 5 Tools

Each tool has its own detailed spec. Build order matches the file numbering.

| # | Agent | Persona | Target | Build | Spec |
|---|-------|---------|--------|-------|------|
| 01 | Build Company List | Growth Team | 500 executions | Week 1 | [agents/01-company-list.md](agents/01-company-list.md) |
| 02 | Sales Business Plan | CMO / CRO | 50 ICP companies | Week 2 | [agents/02-sales-business-plan.md](agents/02-sales-business-plan.md) |
| 03 | Best Campaigns to Launch | CMO / CRO | 50 ICP companies | Week 3 | [agents/03-best-campaigns.md](agents/03-best-campaigns.md) |
| 04 | Prepare Your Sales Meeting | Sales (AE / SDR) | 500 executions | Week 4 | [agents/04-meeting-prep.md](agents/04-meeting-prep.md) |
| 05 | Cold Email Copy Review | Sales (SDR / AE) | 500 executions | Week 4 | [agents/05-cold-email-review.md](agents/05-cold-email-review.md) |

---

## 6. CRM Lead Push (Scala CRM)

Every email capture triggers a push to Scala CRM **before** the agent runs:

```json
{
  "email": "lead@company.com",
  "first_name": "Alex",
  "tool_used": "cold_email_review",
  "tool_input_summary": "domain: acme.io | email: 87 words",
  "company_domain": "acme.io",
  "language": "en",
  "utm_source": "linkedin",
  "utm_campaign": "cold-email-review-q2-2026",
  "utm_medium": "paid_social",
  "ref": "yazid",
  "run_number": 1,
  "shareable_link_generated": false,
  "created_at": "2026-05-05T10:23:00Z"
}
```

Tool-specific fields added per tool (e.g. `target_company_domain` for Meeting Prep, `icp_prompt` for Company List).

---

## 7. Loading UX — Narrative Live (Typewriter Intel)

During agent generation (10–30s), the UI displays a live typewriter feed of what the agent is actually doing.

**Pattern:**
```
🔍 Analyzing getscalability.io...
   → B2B sales intelligence · outbound focus detected
🔍 Looking up HubSpot in our database...
   → 6,400 employees · Series D confirmed
🔍 Pulling campaign benchmarks...
   → 312 similar campaigns analyzed
⚡ Building your briefing...
```

**Steps per tool:**

| Tool | Step sequence |
|------|--------------|
| Cold Email Review | Analyzing your domain → Evaluating email structure → Scoring 11 dimensions → Rewriting |
| Meeting Prep | Analyzing your domain → Looking up [company] → Pulling benchmarks → Building briefing |
| Company List | Parsing your ICP → Searching Scala API → Scoring + filtering → Ranking 50 accounts |
| Sales Business Plan | Looking up your company → Pulling industry benchmarks → Building financial model → Calculating deliverability |
| Best Campaigns | Finding similar campaigns → Analyzing performance patterns → Detecting signals → Customizing angles |

If a step fails: `⚠️ Limited data — continuing with available signals` and agent proceeds with fallback.

---

## 8. Output Rendering — Hybrid Streaming + Structured

**Phase 1 — Streaming text (SSE)**
Output appears token by token after the loading narrative. Builds on the intelligence surfaced during loading.

**Phase 2 — Snap to structured cards**
Once streaming completes, output re-renders into formatted sections, score badges, tables, and action blocks.

---

## 9. Error Handling

### 9.1 Invalid / Unresolvable Domain
Client-side regex validation on blur + server-side DNS check on submit. Agent never runs.
```
❌ "We couldn't find a website at [domain].
    Double-check the URL (no https:// needed)."
```

### 9.2 Company Not Found via Scala API
Agent continues with domain scrape + Claude knowledge. Output generated with quality flag.
```
⚠️ "[Company] isn't in our database yet.
    This output is based on public information
    and may be less precise than usual."
```

### 9.3 Company List Returns < 50 Results
Show N results found + 3 pre-generated "broaden" options (generated by agent in same run, no extra API call).
```
We found [N] companies matching your exact criteria.

💡 Want more?
   [Remove size filter →]          ~+18 companies
   [Expand to include Series A →]  ~+12 companies
   [Broaden to EU + US →]          ~+25 companies
```

### 9.4 Agent Timeout (> 45s)
Partial results saved server-side for 10 minutes. Retry is instant.
```
⏱️ "This is taking longer than expected."
   [See partial results]  [Try again]
```

### 9.5 Rate Limit Reached
```
You've used your 3 free runs this month.
Resets on [date].

Or get unlimited access → [Book a demo]
```

---

## 10. Copy — Hardcoded EN/FR (v1)

All landing page and widget copy is hardcoded in the React components in both languages.

**Language detection:** `navigator.language` on load → default EN or FR. Manual toggle available in widget header.

**Scope of hardcoded copy per tool:**
- Hero headline + subline
- Input field labels + placeholder text
- Gate form copy ("Enter your email to unlock your results")
- CTA button labels
- Error messages
- Loading step labels (typewriter intel text)
- Cross-tool CTA labels

*Notion CMS (dynamic copy editing without redeploy) deferred to v2.*

---

## 11. Hub Page

Single hub page listing all 5 tools organized by persona:

```
┌────────────────────────────────────────────────────────┐
│  AI Tools by Scalability                               │
│  Free. Powered by real campaign data.                  │
│                                                        │
│  For Sales          For Growth      For CMO / CRO      │
│  ──────────         ──────────      ──────────────     │
│  📧 Email Review    🏢 Company List  📊 Sales Plan      │
│  🤝 Meeting Prep                    🚀 Best Campaigns   │
└────────────────────────────────────────────────────────┘
```

Each card: tool name, one-line description, persona tag, "Try free →" CTA.

---

## 12. V1 Build Order (Solo, ASAP)

### Week 1 — Company List
**Why first:** Core Scala API pipeline, SSE streaming, email gate, and PostgreSQL rate limiting built here are reused by all subsequent tools. Infrastructure (gate, CRM push, SSE streaming, shareable link, PostgreSQL rate limiting) built once and reused by all tools.

Deliverables:
- FastAPI backend + SSE streaming
- Email gate + PostgreSQL rate limiting
- Scala CRM push
- Result permalink storage (PostgreSQL)
- React widget (EN + FR hardcoded)
- Scala API calls (no cross-stack dependency on ai-agents)
- ICP prompt → search → rank pipeline
- Simple table output + CSV export

### Week 2 — Sales Business Plan
**Why second:** Self-contained (Scala API + domain scrape + Claude). No dependency on week 1's Scala pipeline.

Deliverables:
- Scala API queries for industry benchmarks
- Deliverability calculator logic
- Gotenberg PDF generation + branded template
- Domain HTTP scrape (LinkedIn URL resolved via Scala API profile lookup)
- Structured output sections (streaming → cards)

### Week 3 — Best Campaigns
**Why third:** Requires Lemlist Pinecone index setup. Most complex data pipeline. Notion MCP export.

Deliverables:
- Pinecone indexing of Lemlist campaign data (subject + body + stats per step)
- Semantic search over campaign index
- Lemlist performance benchmark queries (PostgreSQL)
- Notion MCP export integration
- 8-campaign card output

### Week 4 — Meeting Prep + Cold Email Review
**Why last:** Meeting Prep reuses Scala API pipeline from week 1. Cold Email Review is self-contained (domain scrape + Claude only) — simplest tool technically, saved for last.

Deliverables (Meeting Prep):
- Company profile enrichment via Scala API
- Cross-tool CTAs with context passing

Deliverables (Cold Email Review):
- Copywriting-analyzer framework wired to Claude
- Domain HTTP scrape for offer context
- 11-dimension scoring + structured rewrite output

---

## 13. Open Questions

| Question | Status |
|----------|--------|
| Deployment target (Webflow embed vs. Next.js subdomain) | TBD |
| Scala CRM staging down — confirm prod endpoint | Check with team |
| Lemlist Pinecone index: needs to be created in ai-lead-magnet or shared with ai-agents? | Architecture decision |
| Charles Trenot's Sales Business Plan doc — deliverability reference values | Yazid to provide |
| LinkedIn Ad UTM naming convention | TBD with marketing |
| RGPD: privacy policy link + consent text on gate form | ✅ Resolved — implicit consent copy below submit button (see §3) |

---

## 14. Success Metrics

| Tool | Target | Metric |
|------|--------|--------|
| Cold Email Review | 500 | Unique executions (emails captured) |
| Meeting Prep | 500 | Unique executions (shared pool) |
| Company List | 500 | Unique executions |
| Sales Business Plan | 50 | Unique ICP companies |
| Best Campaigns | 50 | Unique ICP companies (shared pool) |
| All tools | — | Visit → email capture rate > 35% |
| All tools | — | Return usage (2nd+ run, same email) > 20% |
| Best Campaigns | — | Notion export rate > 30% of unlocked users |
