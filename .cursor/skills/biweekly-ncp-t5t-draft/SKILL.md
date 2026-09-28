---
name: biweekly-ncp-t5t-draft
description: >-
  Drafts "Top 5 Things - NCP | EMEA | SA" customer updates from Outlook, Slack,
  Confluence, Teams, Salesforce, and the local NCP RD DC Dashboard (localhost:5175).
  Boris-style compact sections. Hunts DC/site readiness signals (power, CDU
  commissioning, rack install, site visits, offtaker) and NCP qualification
  signals (demand, power, operated stack, ISP/inference-platform funding). Use when the user asks for
  biweekly T5T, Top 5 Things NCP EMEA SA, folder-based account digests, or recurring
  account email drafts from specific mailbox folders under Customers.
---

# Biweekly NCP Top 5 (T5T) draft

## Goal

Produce **draft sections** (and optional full email shell) for **Top 5 Things - NCP | EMEA | SA**, one **customer block** per account. Default cadence: **since the user’s last sent T5T** (found in **Sent Items**), or an explicit `start_date`.

## NCP qualification lens (always apply)

**Market context:** Inference platforms (ISPs / anchor tenants) are getting **funded at scale**. Treat offtaker + ISP pairing, PO/allocation, and investor/funding threads as first-class signals — not just “future customer interest.”

**Qualification bar:** NCP qualification now needs **demand + power + operated stack** — all three, not hardware-only:

| Pillar | What to hunt | Where it usually shows up |
|--------|--------------|---------------------------|
| **Demand** | Anchor offtaker / ISP tenant, workload tenant, PO or allocation path, opp stage, contracted capacity, investor secured | **Offtake**, mail-referenced SFDC opps, Christophe/AM trip reports |
| **Power** | MW / utility power, PUE, main power, UPS, backup-power SLA, site feasibility, construction timeline | **Capacity coming online**, Epic power-planning threads, dashboard ARB DC fields |
| **Operated stack** | DSX OS / managed K8s substrate, NICo/NVSentinel, provisioning path, multitenancy, storage/network validation, break-fix / inventory / telemetry readiness | **Technical**, **Cloud**, dashboard DSX OS + GB300 ARB software inputs |

**Authoritative reference (do not invent requirements beyond sources):**
[NVIDIA Inference Provider Platform Requirements for NCPs](https://docs.nvidia.com/dsx/ncp/inference-provider-requirements/home) — GB300 NVL72 cluster the NCP **operates** (substrate) so ISPs can deploy inference platforms on managed Kubernetes. NCP owns facility adherence (RD-1), hardware validation (HW-*), networking/multi-tenancy (NET-*), storage (STR-*), managed K8s / KaaS (KUB-*), inventory & telemetry; ISP owns the inference software stack above the cluster boundary.

When drafting, **call out gaps explicitly** (e.g. “power planning active but operated-stack / DSX OS owner not locked”) rather than implying qualification is complete.

## Preconditions

- **MaaS Outlook** MCP healthy (`outlook_health_check`). If it fails, stop and tell the user to refresh ECI auth; do not invent mail content.
- **ECI policy**: only **@nvidia.com** mail is fully visible. When `filteredCount` is returned, state that explicitly and warn that customer-only threads may be missing.

## Inputs to confirm (ask if missing)

1. **Folders** — explicit Outlook `folder_name` display names (e.g. `Nebul`, `Verda (DataCrunch)`). Child folders under **Customers** must be queried separately; if folder resolution fails, fall back to `outlook_search_messages` per account keyword across Inbox + Sent + subfolders.
2. **Time window** — latest **Sent Items** message whose subject contains `Top 5 Things`, `NCP`, `EMEA`, `SA` → **T0**; query mail **after T0** (default: next calendar day through today).
3. **Recipients** — user copies **To/Cc** in Outlook; skill drafts **body** only unless addresses are given.

## Multi-source workflow (run for each account)

Every run must check all six source groups below: Outlook Inbox, Sent Items, and
account-related subfolders; Slack; Confluence; Teams; Salesforce; and the local
NCP RD DC Dashboard. A source failure is reported as a coverage gap, never
silently skipped.

## Coverage recovery (mandatory before any gap line)

Do not finish a draft with "Slack was not signed in", "Teams / Confluence /
Salesforce unavailable", "dashboard was down", or "Epic's folder did not
resolve" until the matching recovery below has been tried. A failed MCP health
check is not a failed query. Use the CLI fallback, then query.

| Gap | Recovery, in order |
|-----|--------------------|
| Outlook MCP down or a folder 404s | `outlook-cli` on the shared Entra cache. If `Epic`, `Epic Group`, or `I3D` does not resolve, `outlook-cli folder list` and match the real display name, then `--all-folders --query` for that account since T0. |
| Slack MCP down or unsigned | `slack-cli auth status`. If unsigned, `slack-cli auth init`, give the user the URL, then `slack-cli auth complete '<callback-url>'`. Search only after auth succeeds. If `maas.prd.astra.nvidia.com` does not resolve, retry once and report the DNS failure. Do not write "Slack was not signed in" for a DNS failure. |
| Confluence MCP down | `confluence-cli auth status`, then `confluence-cli` search. If no API token is stored, the one allowed gap line is the exact `confluence-cli auth set-token` step. Do not skip the search when a token exists. |
| Teams MCP down | `teams-cli` (same Entra cache as Outlook). `teams-cli chat list` and read chats whose topic matches an account since T0. |
| Salesforce MCP discovery fails | Still run `sfdc-cli search` / `sfdc-cli query`. Do not treat a failed `capability.mcp-tools` check as an empty pipeline. |
| Dashboard port 5175 down | Serve `scripts/serve_dashboard_5175.py` from `_dashboard_5175.html`, confirm HTTP 200, parse, and label it a snapshot with the `Last refresh` value. Stale seed never overrides fresher mail. |
| Epic missing | Try `Epic`, `Epic Group`, and `Epic Games`, then a mailbox-wide `Epic` search since T0. Say which name was used. Absence after that search is "no new signal", not an unresolved folder. |

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
curl.exe -s -o NUL -w "%{http_code}" --max-time 10 http://127.0.0.1:5175/
curl.exe -s --max-time 15 http://127.0.0.1:5175/ -o _dashboard_5175.html
python scripts/parse_dashboard_5175.py
```

If port 5175 is down, first try the dashboard's normal launcher when its source
project is available. Otherwise recover read-only access to the last captured
snapshot and verify HTTP 200:

```powershell
Start-Process python -ArgumentList "scripts/serve_dashboard_5175.py" -WorkingDirectory (Get-Location) -WindowStyle Hidden
curl.exe -s -o NUL -w "%{http_code}" --max-time 10 http://127.0.0.1:5175/
```

Label this fallback explicitly as a **snapshot**, including the dashboard's
`Last refresh` value. Never present snapshot recovery as a successful live
daily automation run.

Or parse saved HTML for:

- **Overview table**: Account, Status (Green/Yellow/Red), Top Priority, Owner, Blocker, Due.
- **Account Room**: Signals Made, Asks, Next Steps, Outreach (per account article).

**How to use in T5T:**

- Treat dashboard as **supplementary** — check `Last refresh` banner (e.g. *seed baseline, 30 Jun 2026* vs live daily run).
- **Prefer Outlook/Slack** for offtake/PO/commercial facts when dashboard is seed-only or stale.
- **Strong fit for Capacity coming online / Technical** when dashboard lists: GB300 ARB inputs, DC location, rack layout, **main power**, UPS, **CDU/liquid cooling**, PG25 storage, construction timeline, site readiness checklist.
- Do **not** let stale seed rows override fresh mail (e.g. Nebul “insufficient signal” when mail shows active Romania/JD.com threads).

**Default 8 accounts on dashboard:** I3D/Ubisoft, Epic Group, OVH/OVHcloud, Infra2tokens, G-Core/Gcore, Fossefall, Verda/DataCrunch, Nebul.

**Related project aliases (always search with the account):**

- **G-Core** — also Aleria, AMI Labs / AMI Lab, Amsterdam / AMS1 / Serverfarm, Mbuzz. Keep Eryce AG distinct from Aleria AMS.
- **Fossefall** — also Norway, Fyresdal / Fyresdhal, Armada / Leviathan MDC. Keep Sweden / Stockholm GB300 distinct from Norway.

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
| **ISP / inference platform** | inference platform, ISP, inference service provider, managed Kubernetes for tenant, Dynamo/production inference, funding secured, investor |
| **Operated stack** | DSX OS, managed Kubernetes, KaaS, NICo, NVSentinel, GPU Operator, multitenancy, inventory service, break-fix, provisioning, IaaS OS install |

**Map to Boris sections:**

- **Offtake** — PO/allocation, offtaker/ISP pairing, **demand** pillar (funding / investor / anchor tenant secured).
- **Capacity coming online** — site readiness, main power, MW/DC dates, rack install/cabling, dashboard ARB/DC readiness gaps — **power** pillar.
- **VR NVL72 prep** — GB300/NVL72 rack delivery, validation, RA.
- **Technical** — CDU commissioning, site visits, BoM, Slack, NVIS, **operated stack** (DSX OS, NICo, managed K8s substrate, storage/network validation) — cross-check [Inference Provider Requirements](https://docs.nvidia.com/dsx/ncp/inference-provider-requirements/home) when gaps are flagged.
- **Cloud** — production inference stack, Dynamo, multitenancy, ISP-ready platform signals.
- **Future plans** — next commissioning gate, ARB completion, scheduled meetings; close **demand + power + operated stack** gaps.

If none appear for the window, say so under **Capacity coming online** (power) or **Technical** (operated stack) as appropriate.

**Per-account qualification sanity check (internal — one line in mind per account):**
- Demand: confirmed offtaker/ISP or funding path? Y / partial / no signal
- Power: MW/site/power plan credible for scale? Y / partial / no signal
- Operated stack: DSX OS / managed K8s / NICo path owned? Y / partial / no signal

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
- Apply the **demand + power + operated stack** qualification lens; cite [Inference Provider Requirements](https://docs.nvidia.com/dsx/ncp/inference-provider-requirements/home) only when framing operated-stack / ISP-substrate gaps — not as a substitute for account-specific mail.
- **Reconcile conflicts**: fresh Outlook > Slack > Confluence > Salesforce > dashboard seed.
- When folder pull is blocked, say so and note search-based fallback.
- Keep **To/Cc** aligned with prior real sends.

## Optional deliverables

- Save HTML: `t5t-ncp-emea-sa-YYYY-MM-DD.html`
- `outlook_create_draft` with subject `Top 5 Things - NCP | EMEA | SA` (plain text body; user adds recipients)
