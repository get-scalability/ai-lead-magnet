# Agent 02 — Sales Business Plan Generator

**Persona:** CMO / CRO / Head of Sales
**Target:** 50 ICP companies onboarded
**Build:** Week 2
**Slug:** `sales-business-plan`

---

## Input

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Your company domain | Text | Yes | Your own domain — we'll build your outbound sales plan based on your current size and market (e.g. `acme.io`) |
| Context prompt | Free text | No | "Describe your situation or ask for something specific" — hint: "Add context for a more precise plan — e.g. current team size, ARR, specific challenge" |

Agent infers: industry, team size, growth stage, funding. If data is limited, Claude flags it explicitly in the output.

---

## Processing

1. **Scala API** → company profile lookup by domain → returns company name, size, industry, and growth stage
2. **HTTP scrape** of domain → extract offer, positioning, ICP context
3. **Scala API** → industry benchmarks, comparable company data
4. **Claude** → generates full-funnel sales plan using Scalability's playbooks + benchmarks

---

## Loading UX (Typewriter Intel)

```
🔍 Looking up acme.io in our database...
   → SaaS · 45 employees · Series A detected
🔍 Scraping website...
   → Outbound-focused · SMB market · EU region
🔍 Pulling industry benchmarks...
   → 89 comparable companies found in our database
🔍 Building financial model...
   → ACV range: €8K–€25K estimated
⚡ Calculating deliverability standard...
```

---

## Output (streaming → structured sections)

### 1. Team Structure
- Recommended AE / BDR headcount + rationale
- Hiring order and ramp timeline
- Ramp-to-quota period per role

### 2. Financial Model
- Average deal size (inferred from signals + benchmarks, clearly labeled)
- Conversion rates per funnel stage: MQL → SQL → Demo → Close
- Required activity volume: calls/day, demos/week, sequences active
- Target MRR / ARR with 12-month timeline

### 3. Deliverability Standard *(Scalability's unique value)*

Calculator based on target send volume derived from team structure:

```
Target: X emails/day
───────────────────────────────────
Domains needed:        N
Mailboxes per domain:  3
Total mailboxes:       N × 3
Warmup period:         4–6 weeks
Daily limit/mailbox:   20 emails
Recommended provider:  Google Workspace / Outlook
DNS required:          SPF + DKIM + DMARC
```

### 4. Outbound Infrastructure Checklist
Step-by-step actionable setup:
- [ ] Purchase N domains (variations of main domain)
- [ ] Create 3 mailboxes per domain
- [ ] Configure SPF + DKIM + DMARC on each domain
- [ ] Warm up via lemwarm for 4–6 weeks
- [ ] Set bounce limit threshold: < 3%
- [ ] Ramp sending: 10 → 20 → 40 emails/day/mailbox over 4 weeks

### 5. Export
- **PDF download** via Gotenberg (Scalability-branded — shareable in board meetings)
- **Markdown / plain text** copy

---

## Gate

- Email captured **before** agent runs (see global gate logic)
- Full output visible after email submission (no blur)
- **3 lifetime runs per email** (not monthly — this is the high-value CMO tool)
- On 4th run: "Book a strategy call to get a custom plan →"

---

## CRM Fields (Scala CRM push)

```json
{
  "tool_used": "sales_business_plan",
  "tool_input_summary": "domain: acme.io",
  "company_domain": "acme.io",
  "context_provided": true,
  "run_type": "lifetime"
}
```

---

## Error Handling

### Company Not Found via Scala API
Agent continues. Output is generated from domain scrape + Claude inference. Flagged in output:
```
⚠️ "We couldn't find benchmark data for your industry.
    Financial projections are based on general outbound benchmarks
    and may need adjustment for your specific market."
```

### Domain Unresolvable
```
❌ "We couldn't find a website at [domain].
    Double-check the URL (no https:// needed)."
```

---

## Cross-tool CTAs (post-output)

- → "Now find the companies to target with this plan" [link to Company List]
- → "Get your best campaign angles for this team" [link to Best Campaigns]
