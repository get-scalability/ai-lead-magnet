# Agent 03 — Best Campaigns to Launch

**Persona:** CMO / CRO
**Target:** 50 ICP companies onboarded (shared pool with Sales Business Plan)
**Build:** Week 3
**Slug:** `best-campaigns`

---

## Input

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Your company domain | Text | Yes | Scraped to understand your offer and ICP — so campaign hooks are relevant to what you sell |
| Target company domain | Text | Yes | The company you're building campaigns for |
| Context prompt | Free text | No | "Describe your current outbound situation" — encouraged, improves output quality |

---

## Processing — Lemlist Data + Scala API

### Historical performance layer (Lemlist PostgreSQL + Pinecone)

1. Query `lemlist_campaign` + `lemlist_campaign_stat` → find campaigns with high reply rates for similar industry / stage / persona
2. Query `lemlist_step` → retrieve actual email copy (subject + body) of top-performing campaigns
3. **Pinecone semantic search** over indexed Lemlist campaign copy → "find campaigns similar to this company's context"
4. Derive benchmarks: reply rates by angle, industry, seniority, channel, sequence position

> **Data available in Lemlist sync:**
> - `LemlistStep.subject` + `LemlistStep.body` — actual email copy per step
> - `LemlistCampaignStat.metric` + `.value` — per-campaign, per-channel, per-step performance metrics
> - Campaign name, labels, status

### Company context layer (Scala API + domain scrape)

- **HTTP scrape** of your domain → extract your offer, ICP, and positioning
- **Scala API** → target company profile lookup by domain → returns company name, size, industry, ICP score, LinkedIn URL, hiring signals, recent leadership changes, and growth indicators
- **HTTP scrape** of target domain + LinkedIn page → recent announcements, tech stack hints

### Hybrid generation

Agent identifies the top-performing historical campaigns matching the company's profile, then customizes the angle, hook, and messaging for the company's current context and signals.

---

## Loading UX (Typewriter Intel)

```
🔍 Analyzing getscalability.io...
   → B2B sales intelligence · outbound-focused
🔍 Looking up acme.io in our database...
   → SaaS · Series B · 120 employees · EU market
🔍 Searching campaign history...
   → 312 campaigns run for similar companies
🔍 Identifying top performers...
   → Best angle: "SDR hiring trigger" → 4.2% reply rate
🔍 Detecting current signals...
   → VP Sales joined 6 weeks ago · 3 open SDR roles
⚡ Customizing 8 campaign angles for your context...
```

---

## Output — 5–8 Campaign Recommendations

Per campaign card:

| Field | Description |
|-------|-------------|
| **Campaign name + angle** | Short label (e.g. "SDR Ramp Speed") + one-line angle |
| **Target persona** | Role + why now (tied to current signals) |
| **Channel mix** | Email / LinkedIn / Cold call |
| **Hook** | Personalized opening line example using detected signals |
| **Why it works for this company** | Specific to signals detected — not generic |
| **Performance benchmark** | e.g. "~3.8% reply rate for SaaS at Series B — from our campaign history" |
| **Sequence structure** | Number of touchpoints + timing + channel rotation |

---

## Gate + Export

- Email captured **before** agent runs (see global gate logic)
- All 8 campaigns visible after email submission
- **3 runs per email per month**

**Export options (post-gate):**
- **Push to Notion** via Notion MCP — direct write to user's Notion workspace as structured blocks
- **Download as markdown / plain text**
- **Associate with Scala segment or campaign** (direct CRM action)

---

## CRM Fields (Scala CRM push)

```json
{
  "tool_used": "best_campaigns",
  "tool_input_summary": "your domain: getscalability.io | target: acme.io",
  "company_domain": "getscalability.io",
  "target_company_domain": "acme.io",
  "context_provided": false,
  "campaigns_generated": 8,
  "notion_export": false
}
```

---

## Error Handling

### Company Not Found via Scala API
Output generated from domain scrape + Lemlist benchmarks + Claude. Flagged in output:
```
⚠️ "Limited data found for [company] in our database.
    Campaign recommendations are based on web signals
    and industry benchmarks."
```

### Lemlist Data Insufficient (< 5 comparable campaigns found)
Fall back to Claude + Scalability playbooks. Benchmarks labeled as "industry estimate" instead of "from our campaign history." **Minimum 5 campaigns generated in all cases.**

---

## Cross-tool CTAs (post-output)

- → "Review your cold email for [top campaign angle]" [link to Cold Email Review]
- → "Build the target list for this campaign" [link to Company List, ICP pre-filled from signals]

---

## Technical Notes

- **Pinecone index** for Lemlist campaigns needs to be created in `ai-lead-magnet` (or shared with `ai-agents` — architecture decision pending, see open questions in spec)
- Index fields: `campaign_id`, `step_index`, `subject`, `body`, `reply_rate`, `industry`, `stage`, `persona_seniority`
- Semantic search query: company context + ICP description → nearest neighbor campaigns
