"""
Generate a weekly markdown report for NVIDIA ncx-infra-controller-core (NICo).

Includes:
  - Git commits and touched paths for the window
  - A stable solution topology (Mermaid) + plain-English layer cake
  - "Topology vs. this week's changes" mapping path prefixes → subsystems

Usage (from ncp-inference-demos repo root):
  python workspace/Projects/ncx-infra-controller-core/scripts/gen_weekly_report.py
  python .../gen_weekly_report.py --days 14 --repo D:/src/ncx-infra-controller-core

Requires git on PATH.
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
PROJECT = SCRIPT.parents[1]
REPO_ROOT = SCRIPT.parents[4]
DEFAULT_REPO = REPO_ROOT / "external" / "ncx-infra-controller-core"
REPORTS = PROJECT / "reports"

# Path prefix → (subsystem name, one-line plain English)
PATH_TOPOLOGY: list[tuple[str, str, str]] = [
    ("deploy/carbide-base/api", "Site Controller — carbide-api", "Kubernetes deployment for the gRPC control plane (port 1079)."),
    ("crates/api", "NICo Core — API service", "Rust binary + domain logic: state machines, tenancy, calls into DB and workers."),
    ("crates/api-db", "NICo Core — persistence", "SQL schema / migrations backing long-lived machine and site state."),
    ("deploy/carbide-base/dhcp", "Site Controller — DHCP", "Authoritative Kea DHCP for underlay/tenant pools."),
    ("crates/dhcp", "DHCP integration", "Code that drives Kea configs and DHCP behavior expected by the core."),
    ("deploy/carbide-base/dns", "Site Controller — DNS", "Split DNS: carbide-dns + recursive path via unbound."),
    ("crates/dns", "DNS services", "Authoritative / forwarding glue for `.forge` and site names."),
    ("deploy/carbide-base/pxe", "Site Controller — PXE", "Network boot delivery and boot artifact plumbing."),
    ("pxe/", "PXE artifacts / images", "mkosi profiles, initramfs roots, scout loaders."),
    ("deploy/carbide-base/hardware-health", "Site Controller — hardware health", "Scrapes Prometheus-style metrics from hosts and feeds state upstream."),
    ("deploy/carbide-base/ssh-console-rs", "Site Controller — SSH console", "Virtual serial / console aggregation and logging."),
    ("crates/ssh-console", "SSH console service", "Rust service bridging BMC serial to operators and logs."),
    ("deploy/carbide-base/dsx-exchange-consumer", "DSX exchange consumer", "Sidecar style consumer for exchange / event feeds."),
    ("crates/rpc", "gRPC / Protobuf contracts", "IDL and client/server stubs shared across components."),
    ("deploy/", "Kubernetes manifests", "Kustomize bases/overlays: how NICo is wired on-cluster."),
    ("helm/", "Helm charts", "Packaged installs (e.g. carbide-bmc-proxy and friends)."),
    ("bluefield/", "BlueField telemetry", "OTel processors/receivers for DPU-adjacent stats."),
    ("crates/dpu-agent", "DPU agent", "On-DPU daemon that pulls configuration from NICo core over the secure fabric."),
    ("book/", "Operator documentation", "mdBook sources published to GitHub Pages."),
]


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        return ""
    return r.stdout.strip()


def _week_bounds(days: int) -> tuple[dt.date, dt.date, str, str]:
    end = dt.date.today()
    start = end - dt.timedelta(days=days - 1)
    iso = end.isocalendar()
    week_label = f"{iso.year}-W{iso.week:02d}"
    return start, end, week_label, f"{start.isoformat()} – {end.isoformat()}"


def _path_under_prefix(path: str, prefix: str) -> bool:
    """True if path equals prefix or is a file/dir under prefix (not `api` vs `api-db`)."""
    pre = prefix.rstrip("/")
    if path == pre:
        return True
    return path.startswith(pre + "/")


def _map_paths(paths: set[str]) -> list[tuple[str, str, str]]:
    """Longest matching prefix wins."""
    rules = sorted(PATH_TOPOLOGY, key=lambda row: len(row[0]), reverse=True)
    hits: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for p in sorted(paths):
        for prefix, name, desc in rules:
            if _path_under_prefix(p, prefix):
                if name not in seen:
                    seen.add(name)
                    hits.append((prefix, name, desc))
                break
    return hits


def _collect_paths(repo: Path, since: str) -> set[str]:
    raw = _git(repo, "log", f"--since={since}", "--pretty=format:", "--name-only")
    paths: set[str] = set()
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("commit "):
            continue
        paths.add(line)
    return paths


def _commits(repo: Path, since: str) -> list[str]:
    out = _git(
        repo,
        "log",
        f"--since={since}",
        "--pretty=format:%h %ad %s",
        "--date=short",
        "-n",
        "50",
    )
    return [ln for ln in out.splitlines() if ln.strip()]


def build_markdown(repo: Path, days: int) -> str:
    start, end, week_label, span = _week_bounds(days)
    since = start.isoformat() + " 00:00:00"
    head = _git(repo, "rev-parse", "HEAD") or "unknown"
    short = _git(repo, "rev-parse", "--short", "HEAD") or "?"

    commits = _commits(repo, since)
    paths = _collect_paths(repo, since)
    mapped = _map_paths(paths)

    if not commits:
        commits_note = "_No commits in this window (shallow clone with one commit, or quiet week)._"
        commits_body = commits_note
    else:
        commits_body = "\n".join(f"- `{c}`" for c in commits)

    if paths:
        paths_body = "\n".join(f"- `{p}`" for p in sorted(paths)[:80])
        if len(paths) > 80:
            paths_body += f"\n- _…and {len(paths) - 80} more paths_"
    else:
        paths_body = "_No file paths collected (try `git fetch --unshallow` for full history)._"

    topo_delta = ""
    if mapped:
        topo_delta = "\n".join(
            f"| `{pfx}` | **{name}** | {desc} |" for pfx, name, desc in mapped
        )
        topo_delta = "| Changed area (prefix) | Topology node | In one sentence |\n|---|---|---|\n" + topo_delta
    else:
        topo_delta = "_No direct mapping from changed paths to known subsystems (see full path list below)._"

    return f"""# Weekly report — NCX Infra Controller Core (NICo)

**Week label:** {week_label}  
**Calendar span:** {span}  
**Upstream HEAD:** `{short}` (`{head}`)  
**Repo:** https://github.com/NVIDIA/ncx-infra-controller-core  

---

## 1. Executive pulse

- **What this system is (one sentence):** NICo is the **site-local robot** that turns racked bare metal into **cataloged, trusted, network-bootable** machines—without someone hand-DHCP’ing, hand-imaging, or hand-tracking firmware on every box.
- **How it stays safe:** Components talk over **mTLS’d gRPC**; DPUs and BMC paths are used so the **host is not trusted** until the control plane says it is.
- **What moved this week (from git):** see §3. If the list looks short, widen the window (`--days 14`) or deepen your clone (`git fetch --unshallow`).

---

## 2. Current solution topology

### 2.1 Picture in your head (plain English)

Think of **three layers**:

1. **North / human & cloud:** Operators and automation hit **NICo REST** (separate repo) or **Site Agent** (Temporal northbound). Those requests become **gRPC** into the core running on the site cluster.
2. **Middle / “site controller” on Kubernetes:** `carbide-api` is the **brain** (state in Postgres, secrets in Vault, identities via cert-manager/SPIFFE). Around it sit **DHCP**, **DNS**, **PXE**, **hardware health**, **SSH console**—each is a specialist daemon the brain coordinates.
3. **South / metal:** Each server is **host + BlueField DPU**. The DPU runs **`dpu-agent`**, pulls instructions from the core, and keeps **out-of-band** paths alive so the cluster can see health and push boots even when the host OS is broken or blank.

**Simple rule:** *REST/cloud asks; core decides; DHCP/DNS/PXE deliver; DPU enforces.*

### 2.2 Technical topology (Mermaid)

```mermaid
flowchart TB
  subgraph North["Northbound & operators"]
    REST["NICo REST (other repo)"]
    SA["Site Agent + Temporal"]
    CLI["Admin CLI (gRPC)"]
  end

  subgraph K8s["Kubernetes site cluster (e.g. forge-system)"]
    API["carbide-api :1079 gRPC"]
    PG[("PostgreSQL / forgedb")]
    V[("Vault PKI + secrets")]
    DHCP["carbide-dhcp / Kea"]
    DNS["carbide-dns + unbound"]
    PXE["carbide-pxe + static artifacts"]
    HH["hardware-health scraper"]
    SSH["ssh-console"]
  end

  subgraph South["Managed rack"]
    H["Host CPU / RAM / disks"]
    DPU["BlueField DPU + dpu-agent"]
    BMC["BMC / Redfish"]
  end

  REST --> SA
  SA --> API
  CLI --> API
  API --> PG
  API --> V
  API --> DHCP
  API --> DNS
  API --> PXE
  API --> HH
  API --> SSH
  DHCP --> H
  PXE --> H
  DNS --> H
  SSH --> BMC
  DPU --> API
  HH --> H
```

### 2.3 Ports & contracts (cheat sheet)

| Surface | Tech | Notes |
|--------|------|------|
| Core API | gRPC over mTLS | SPIFFE-style identities in deploy manifests |
| Metrics | Prometheus text | e.g. hardware-health on `:9009` per book |
| DHCP | UDP/67 | Authoritative for Carbide-managed subnets |
| PXE / HTTP | site-specific | Boot artifacts + static PXE hostnames in `.forge` zone |

---

## 3. This week in the repo (git)

### 3.1 Commits (`--since={since}`)

{commits_body}

### 3.2 Topology vs. changed paths

{topo_delta}

### 3.3 Raw paths (deduped)

{paths_body}

---

## 4. Deep dive — why `carbide-api` sits in the middle

| Technical | Simple |
|-----------|--------|
| Serializable transactions in Postgres with `SELECT … FOR UPDATE` ordering | The database is the **single writer** for “who owns this machine right now” so two operators cannot race and assign the same node twice. |
| gRPC + mTLS to every sidecar | Each helper (DHCP, PXE, …) is **untrusted network-wise** until it presents the right cert—same idea as service mesh identity. |
| DPU agent loop | The DPU is a **small computer you still control** when the main CPU is mis-imaged or hostile—ideal anchor for zero-trust bare metal. |

---

## 5. How to refresh next Friday

```bash
cd external/ncx-infra-controller-core
git pull
cd ../..
python workspace/Projects/ncx-infra-controller-core/scripts/gen_weekly_report.py
```

Optional: merge bullets from `weekly-report-TEMPLATE.md` (customers, blockers) after generation.

---
_Generated by `scripts/gen_weekly_report.py` — machine-assisted draft; human review required._
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7, help="Rolling window length in days")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO, help="Path to git clone")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output markdown path")
    args = parser.parse_args()

    repo: Path = args.repo
    if not (repo / ".git").is_dir():
        print(f"ERROR: not a git repo: {repo}", file=sys.stderr)
        sys.exit(1)

    _, _, week_label, _ = _week_bounds(args.days)
    md = build_markdown(repo, args.days)

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = args.output or REPORTS / f"weekly-{week_label}.md"
    out.write_text(md, encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
