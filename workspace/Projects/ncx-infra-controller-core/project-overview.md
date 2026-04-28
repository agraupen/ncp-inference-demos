# Project Overview — NCX Infra Controller Core (NICo)

---

## Summary

| Field | Value |
|-------|--------|
| **Project** | [ncx-infra-controller-core](https://github.com/NVIDIA/ncx-infra-controller-core) (NICo / Carbide) |
| **Customer** | Internal / NCX bare-metal automation |
| **Status (RAG)** | Track upstream |
| **Priority** | Set per engagement |

---

## Objective & Description

Site-local, zero-trust **bare-metal lifecycle** control plane: inventory, firmware, DHCP/DNS/PXE, power, provisioning, and DPU-mediated isolation. This workspace folder holds **Co-SA-style tracking** (weekly reports, topology notes), not a fork of the product repo.

**Upstream docs:** [NICo book (GitHub Pages)](https://nvidia.github.io/ncx-infra-controller-core/)

---

## Cadence

- **Weekly report:** run `python scripts/gen_weekly_report.py` (default: last 7 days, `external/ncx-infra-controller-core` clone at repo root). Align with `workspace/_memory/config.yaml` → `preferences.update_cadence.weekly` (e.g. Friday).

---

## Key paths (this workspace)

| Path | Purpose |
|------|---------|
| `reports/weekly-*.md` | Generated weekly narratives |
| `scripts/gen_weekly_report.py` | Regenerates report + topology delta from `git` |
| `weekly-report-TEMPLATE.md` | Human sections to merge if Outlook/MCP context is added |

---

## Links

- GitHub: https://github.com/NVIDIA/ncx-infra-controller-core
- NICo REST (separate repo): https://github.com/NVIDIA/ncx-infra-controller-rest
