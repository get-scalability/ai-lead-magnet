# Agent 04 — Prepare Your Sales Meeting

**Persona:** Sales Team (AE / SDR)
**Target:** 500 unique executions (shared pool with Cold Email Review)
**Build:** Week 4
**Slug:** `meeting-prep`

---

## Input

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Your company domain | Text | Yes | Agent scrapes it to understand your offer and positioning |
| Target company domain | Text | Yes | The company you're preparing to meet |

---

## Processing

1. **HTTP scrape** of user's domain → extract their offer, ICP, positioning
2. **Scala API** → target company profile, ICP score, signals, and real contacts with actual roles — personas are populated from real people, not inferred archetypes
3. **Claude** → synthesizes everything into personas + tailored leverage recommendations

**Fallback:** If target company not found via Scala API → output generated from domain scrape + Claude knowledge only, with data quality badge.

---

## Loading UX (Typewriter Intel)

```
🔍 Analyzing getscalability.io...
   → B2B sales intelligence · outbound-focused · SMB/mid-market
🔍 Looking up HubSpot in our database...
   → 6,400 employees · Series D · CRM + marketing platform
🔍 Identifying key personas...
   → 3 relevant profiles found
🔍 Pulling company signals...
   → VP Sales joined 6 weeks ago · 12 open SDR roles
⚡ Building your meeting briefing...
```

---

## Output (streaming → structured cards)

### Key Personas to Target
**2–5 personas** (minimum 2, maximum 5 — based on actual relevance, not padded)

Per persona:
- Role + seniority
- Why they matter for your deal
- Recommended entry point (cold email / LinkedIn / warm intro / call)
- What they care about right now (tied to company signals)

### Company Insights
- Growth signals (hiring trends, funding, expansion)
- Tech stack (known tools — relevant for positioning)
- Org structure (team sizes, recent leadership changes)
- Recent triggers (news, job postings, LinkedIn activity)

### How to Leverage This
Specific recommendations tailored to **your** offer:
- Which signal to open with and why
- Which persona to prioritize first and the angle to use
- What NOT to say (based on their known stack / existing vendors)
- Suggested opening line examples per persona

### Trigger-Based Talking Points
Concrete examples:
- "They hired 12 SDRs in Q1 → mention list quality and ramp time"
- "New VP Sales joined 6 weeks ago → they're building a new playbook, timing is perfect"
- "They use Outreach → reference your integration or differentiation vs. their current stack"

---

## Gate

- Email captured **before** agent runs (see global gate logic)
- Full output unlocked after email submission
- **3 runs per email per month**
- Returning users within limit: skip gate form

---

## CRM Fields (Scala CRM push)

```json
{
  "tool_used": "meeting_prep",
  "tool_input_summary": "your domain: getscalability.io | target: hubspot.com",
  "company_domain": "getscalability.io",
  "target_company_domain": "hubspot.com",
  "personas_found": 3
}
```

---

## Error Handling

### Target Company Not Found via Scala API
Agent continues with domain scrape + Claude. Output generated with badge:
```
⚠️ "HubSpot isn't in our database yet.
    This briefing is based on public information
    and may be less precise than usual."
```

### Your Domain Unresolvable
```
❌ "We couldn't find a website at [your domain].
    Double-check the URL (no https:// needed)."
```

### Target Domain Unresolvable
```
❌ "We couldn't find a website at [target domain].
    Check the URL and try again."
```

---

## Cross-tool CTAs (post-output)

- → "Review your cold email for [Company]" [link to Cold Email Review — no context pre-filled]
- → "Build a list like [Company]" [link to Company List — ICP pre-filled from company signals]
