---
name: biweekly-ncp-t5t-draft
description: >-
  Drafts "Top 5 Things - NCP | EMEA | SA" customer updates from Outlook, Slack,
  Confluence, Teams, Salesforce, and the local NCP RD DC Dashboard (localhost:5175).
  Boris-style compact sections. Hunts DC/site readiness signals (power, CDU
  commissioning, rack install, site visits, offtaker). Use when the user asks for
  biweekly T5T, Top 5 Things NCP EMEA SA, folder-based account digests, or recurring
  account email drafts from specific mailbox folders under Customers.
---

# Biweekly NCP Top 5 (T5T) draft

## Goal

Produce **draft sections** (and optional full email shell) for **Top 5 Things - NCP | EMEA | SA**, one **customer block** per account. Default cadence: **since the user’s last sent T5T** (found in **Sent Items**), or an explicit `start_date`.

## Preconditions

- **MaaS Outlook** MCP healthy (`outlook_health_check`). If it fails, stop and tell the user to refresh ECI auth; do not invent mail content.
- **ECI policy**: only **@nvidia.com** mail is fully visible. When `filteredCount` is returned, state that explicitly and warn that customer-only threads may be missing.

## Inputs to confirm (ask if missing)

1. **Folders** — explicit Outlook `folder_name` display names (e.g. `Nebul`, `Verda (DataCrunch)`). Child folders under **Customers** must be queried separately; if folder resolution fails, fall back to `outlook_search_messages` per account keyword across Inbox + Sent + subfolders.
2. **Time window** — latest **Sent Items** message whose subject contains `Top 5 Things`, `NCP`, `EMEA`, `SA` → **T0**; query mail **after T0** (default: next calendar day through today).
3. **Recipients** — user copies **To/Cc** in Outlook; skill drafts **body** only unless addresses are given.

## Multi-source workflow (run for each account)

### 1. Outlook (primary)

1. `outlook_list_messages` per folder with `start_date`, `end_date`, `limit` 100, `sort_order` desc; page with `cursor` (max 3 pages).
2. Also `outlook_search_messages` per account across mailbox (covers Inbox + Sent + subfolders when folder names fail).
3. Prefer **internal** threads; summarize subjects, dates, `bodyPreview`. Use `outlook_get_message` only for a few high-signal threads (ECI may 404 on some IDs).
4. `outlook_get_conversation` for RE:/Fw: thread context when needed.

### 2. Slack (`user-MaaS Slack` MCP)

- `slack_search_messages` with account name + site-readiness terms (`commissioning`, `CDU`, `site readiness`, `offtaker`, `handover`).
- Respect ECI `filteredCount`; stop on `success=false`.
- Map Slack hits to **Technical** or **Capacity coming online**.

### 3. Confluence (`user-MaaS Confluence` MCP)

- `confluence_search` per account: `"<Account> NCP"`, `"<Account> GB300 site readiness"`, `"<Account> reference architecture"`.
- Prefer **SKB** / **NCP Reference Design Matrix** hits for **VR NVL72 prep** and **Technical**.
- Use `confluence_get_page` only for 1–2 high-signal pages if snippets are thin.
- Note page `updateTime`; flag if >12 months old.

### 4. Teams (`user-MaaS Teams` MCP)

- **Auth first**: if tools are unavailable, call `mcp_auth` on `user-MaaS Teams` (empty `{}`), then retry.
- Search meeting/call threads for account names + readiness keywords when Teams search tools are available post-auth.
- If Teams MCP remains auth-blocked, note the gap in the draft footer.

### 5. Salesforce

**Preferred (when MaaS Salesforce MCP is enabled):** search Opportunities / Accounts for account name, stage, close date, PO/allocation signals.

**Fallback (`managing-salesforce` skill / `sfdc-cli`):**

```bash
sfdc-cli auth status
sfdc-cli search --term "Nebul" --objects '[{"name":"Opportunity","fields":["Id","Name","StageName","CloseDate"]}]' --limit 10 --output json
```

- Map opp names / stages to **Offtake**; do not invent PO numbers not in results.

### 6. Local NCP RD DC Dashboard (`http://localhost:5175`)

Daily **NCP RD DC Dashboard** — account to-dos for hardware, software, DSX OS, and DC readiness.

**Fetch (agent must run locally — remote fetch tools cannot reach localhost):**

```powershell
curl.exe -s --max-time 15 http://127.0.0.1:5175/ -o _dashboard_5175.html
python scripts/parse_dashboard_5175.py
```

Or parse saved HTML for:

- **Overview table**: Account, Status (Green/Yellow/Red), Top Priority, Owner, Blocker, Due.
- **Account Room**: Signals Made, Asks, Next Steps, Outreach (per account article).

**How to use in T5T:**

- Treat dashboard as **supplementary** — check `Last refresh` banner (e.g. *seed baseline, 30 Jun 2026* vs live daily run).
- **Prefer Outlook/Slack** for offtake/PO/commercial facts when dashboard is seed-only or stale.
- **Strong fit for Capacity coming online / Technical** when dashboard lists: GB300 ARB inputs, DC location, rack layout, **main power**, UPS, **CDU/liquid cooling**, PG25 storage, construction timeline, site readiness checklist.
- Do **not** let stale seed rows override fresh mail (e.g. Nebul “insufficient signal” when mail shows active Romania/JD.com threads).

**Default 8 accounts on dashboard:** I3D/Ubisoft, Epic Group, OVH/OVHcloud, Infra2tokens, G-Core/Gcore, Fossefall, Verda/DataCrunch, Nebul.

## DC / site readiness signals (always hunt)

| Theme | Examples |
|-------|----------|
| **Site readiness** | site readiness, readiness progressing, site ready, handover, turn-over |
| **Power** | main power, utility power, MW, PUE, power planning, power capacity |
| **Cooling / CDU** | CDU commissioning, CDU install, cooling loop, chilled water |
| **Commissioning** | commissioning activities, commissioning plan, FAT/SAT, acceptance |
| **Rack install** | racks installed, racking, cabling, cable pull, DC visit, on-site install |
| **Site visit / planning** | site visit complete, site survey, site planning, floor plan, white space |
| **Offtaker / anchor** | offtaker, anchor customer, anchor tenant, end customer, workload tenant |

**Map to Boris sections:**

- **Offtake** — PO/allocation **and** offtaker pairing.
- **Capacity coming online** — site readiness, main power, MW/DC dates, rack install/cabling, dashboard ARB/DC readiness gaps.
- **VR NVL72 prep** — GB300/NVL72 rack delivery, validation, RA.
- **Technical** — CDU commissioning, site visits, BoM, Slack, NVIS, DSX OS, Confluence RD refs.
- **Future plans** — next commissioning gate, ARB completion, scheduled meetings.

If none appear for the window, say so under **Capacity coming online**.

## NVIDIA team line (required per account)

First line of each block after account name:

`(AM: @Name · NCP SA: @Aviv Graupen · …)`

Pull names from mail To/Cc/threads, prior T5T sends, and dashboard owners. If unknown: `(NVIDIA team: not confirmed in internal mail yet)`.

## Output format (compact Boris-style)

User-facing T5T uses **one paragraph per account** (not bullet lists). Pattern:

```
Hi all,

<Account>: (<NVIDIA team line>)
Offtake: …
Cloud: …
Capacity coming online: …
VR NVL72 prep: …
Technical: …
Future plans: …
```

- Separate sub-themes inside **Technical** with semicolons or short labels (e.g. `DSX OS: …; Slack: …; Confluence: …`).
- Use `No material update` / `No new internal signal` when thin — do not pad.
- Close email with `Thanks,` + sender name only (no per-account Lida/Laura footer unless mail supports it).

## Source footer (optional, one line after Hi all)

When useful, note: `Built from Outlook (4 Jul–17 Jul), Slack, Confluence, NCP RD DC Dashboard (localhost:5175, <refresh date>). Teams/Salesforce: <queried | not available>. ECI filters external mail.`

## Cadence: every 2 weeks

**Option A — Cursor Automations:** scheduled cron + prompt referencing this skill and folder list. Confirm Outlook MCP works in Cloud Agents.

**Option B — Calendar reminder:** recurring event with prompt `Run biweekly-ncp-t5t-draft for folders: …`

**Option C — Webhook:** Automation webhook with same prompt.

## Quality bar

- Do not fabricate facts unsupported by retrieved sources.
- **Reconcile conflicts**: fresh Outlook > Slack > Confluence > Salesforce > dashboard seed.
- When folder pull is blocked, say so and note search-based fallback.
- Keep **To/Cc** aligned with prior real sends.

## Optional deliverables

- Save HTML: `t5t-ncp-emea-sa-YYYY-MM-DD.html`
- `outlook_create_draft` with subject `Top 5 Things - NCP | EMEA | SA` (plain text body; user adds recipients)
