# Agent 01 — Build Company List

**Persona:** Growth Team
**Target:** 500 unique executions
**Build:** Week 1
**Slug:** `company-list`

---

## Input

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Your domain | Text | Yes | Used to infer your ICP (e.g. `getscalability.io`) |
| Target prompt | Free text | Yes | Describe your target (e.g. "B2B SaaS in France, 50–500 employees, Series A/B") |

---

## Processing

1. **HTTP scrape** of user's domain → infer their offer and ICP criteria
2. **Scala API** → ICP-scored company search + enrichment matching the prompt
3. **Exclusion logic** → removes known competitors and partners from results
4. Output capped at **50 companies**, ranked by ICP score descending

**Fallback:** If Scala API returns < 50 results → show N found + 3 pre-generated "broaden" options (see Error Handling).

---

## Loading UX (Typewriter Intel)

```
🔍 Analyzing getscalability.io...
   → B2B sales intelligence · outbound focus detected
🔍 Searching our database for matching companies...
   → Applying ICP criteria: SaaS · France · 50–500 employees
🔍 Scoring + filtering results...
   → Excluding 4 known competitors
⚡ Ranking 50 accounts by ICP fit...
```

---

## Output — Simple Table (v1)

| Company | Domain | ICP Score | Industry | Size | Why Selected |
|---------|--------|-----------|----------|------|-------------|

**Table features (v1):**
- Default sort: ICP score descending
- Row count badge: "Showing 10 of 50"
- CSV export with fixed columns (unlocked after email gate)

*Sort/filter/column selector → v2*

---

## Teaser (before email gate)

| | Content |
|-|---------|
| ✅ Visible | First 10 companies fully rendered |
| 🔒 Blurred | Rows 11–50 with badge: "40 more companies hidden" |

---

## Gate

- Email captured **before** agent runs (see global gate logic)
- Full table (50 rows) + CSV download unlocked after email
- **3 runs per email per month**
- Returning users within limit: skip gate form

---

## CRM Fields (Scala CRM push)

```json
{
  "tool_used": "company_list",
  "tool_input_summary": "domain: getscalability.io",
  "icp_prompt": "B2B SaaS in France, 50–500 employees, Series A/B",
  "company_domain": "getscalability.io",
  "results_count": 50
}
```

---

## Error Handling

### Company List Returns < 50 Results
Show N results + 3 pre-generated broaden options (computed in same agent run, no extra API call):
```
We found [N] companies matching your exact criteria.

💡 Want more?
   [Remove size filter →]          ~+18 companies
   [Expand to include Series A →]  ~+12 companies
   [Broaden to EU + US →]          ~+25 companies
```

### Domain Unresolvable
Client-side regex + server-side DNS check. Agent never runs.
```
❌ "We couldn't find a website at [domain].
    Double-check the URL (no https:// needed)."
```

### Scala API Returns 0 Results
```
⚠️ "No companies found matching your criteria.
    Try broadening your description or changing the target region."
```

---

## Cross-tool CTAs (post-output)

- → "Prepare your sales meeting with one of these companies" [link to Meeting Prep, domain pre-filled]
- → "Launch a campaign targeting this list" [link to Best Campaigns]

---

## v2 Improvements

- Sort by any column
- Filter by industry / size range / ICP score threshold
- Column selector for CSV export
- Push list directly to a Lemlist campaign
