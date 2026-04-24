---
name: biweekly-ncp-t5t-draft
description: >-
  Drafts "Top 5 Things - NCP | EMEA | SA" customer updates from Outlook using
  MaaS Outlook MCP (Boris-style sections). Use when the user asks for biweekly T5T,
  Top 5 Things NCP EMEA SA, folder-based account digests, or recurring account
  email drafts from specific mailbox folders under Customers.
---

# Biweekly NCP Top 5 (T5T) draft from Outlook folders

## Goal

Produce **draft sections** (and optional full email shell) for **Top 5 Things - NCP | EMEA | SA**, one **customer block** per **mail folder** the user names (typically under **Customers** in Outlook). Default cadence assumption: **since the user’s last sent T5T** (usually found in **Sent Items**), or an explicit `start_date` if the user provides one.

## Preconditions

- **MaaS Outlook** MCP is enabled and healthy. Start with `outlook_health_check` (no args). If it fails, stop and tell the user to refresh ECI auth; do not invent mail content.
- **ECI policy**: only **@nvidia.com** mail is fully visible. When the API returns `filteredCount` / a note about excluded externals, **state that explicitly** in the draft and warn that customer-only threads may be missing.

## Inputs to confirm (ask if missing)

1. **Folders**: explicit list of `folder_name` values (exact Outlook **display names**), e.g. `Nebul`, `Verda (DataCrunch)`, `Fossefall`, `G-Core`, `Infra2tokens`, `Customers` is not a substitute for child folders—each child is queried separately.
2. **Time window**: default—find latest message in **Sent Items** whose subject contains `Top 5 Things` and `NCP` and `EMEA` and `SA` (adjust if the user’s subject line differs). Use its **sent/received** timestamp as **T0**; query each folder for mail **after T0** (next calendar day or `start_date`/`end_date` in ISO local form per tool rules). If the user gives a date (e.g. `02/04/2026`), confirm **DD/MM vs MM/DD** once if ambiguous.
3. **Recipients**: user copies **To/Cc** in Outlook; the skill drafts **body** only unless the user lists addresses.

## Tool workflow (repeat per folder)

1. `outlook_list_messages` with `folder_name`, `start_date`, `end_date` (if used), `limit` **100**, `sort_order` `desc`.
2. If `nextCursor` is present, page with `cursor` until null or the user’s max pages (default **3** pages per folder unless they ask for exhaustive).
3. Prefer **internal** threads for substance; summarize **subjects**, **dates**, and **bodyPreview**; use `outlook_get_message` **only** for a few high-signal messages (avoid pulling entire folders).
4. For **thread context** (replies, RE:/Fw:), use `outlook_get_conversation` when the user cares about the full back-and-forth of a single topic.

## Output format (Boris-style)

For **each** folder / account, emit:

- **Heading**: folder display name (customer label).
- **Offtake** — commercial / PO / allocation / ordering if visible; otherwise say no internal signal.
- **Cloud** — cloud platform, workload, exemplar, SaaS motion if visible.
- **Capacity coming online** — DC/MW/GPU live dates if visible; else omit or say not in internal mail.
- **VR NVL72 prep** — NVL72 / GB300 / rack / validation / RA if applicable; else skip or "no material update".
- **Technical (Other)** — engineering, networking, BoM, Slack, NVIS, support, entitlements, internal syncs.
- **Future plans** — concrete next steps, owners, meetings already scheduled.

Close with **Lida** (software / tracker / enablement) and **Laura** (gigafactory / physical AI / geo) **only** if the folder mail supports it; otherwise say "no internal signal this period".

## Cadence: "every 2 weeks"

This skill defines **what** to run, not a daemon.

**Option A — Cursor Automations (Cloud Agent):** In Cursor, create an **Automation** with a **scheduled trigger** and a **cron** for every 14 days. Paste a **single user prompt** that says: apply skill `biweekly-ncp-t5t-draft`, list folders `…`, and run the workflow. **Important:** confirm whether your **Outlook MCP** is available to **Cloud Agents** in your org; if not, use Option B.

**Option B — Calendar + manual (reliable with MCP):** Outlook (or OS) **recurring event every 2 weeks**; body contains a one-line instruction: open this repo in Cursor and prompt: `Run .cursor/skills/biweekly-ncp-t5t-draft for folders: …`

**Option C — Webhook:** External scheduler POSTs to a Cursor **Automation webhook** that starts the same cloud agent prompt (same MCP caveat as A).

## Quality bar

- Do not fabricate customer facts not supported by retrieved previews.
- When the folder is **thin**, say so and suggest checking **external** mail in Outlook desktop.
- Keep **To/Cc** aligned with the user’s prior real sends (they can paste last week’s headers once as a template).
