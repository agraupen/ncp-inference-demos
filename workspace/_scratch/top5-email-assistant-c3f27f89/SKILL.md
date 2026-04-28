---
name: top5-email-assistant
description: "Expert assistant for writing NVIDIA 'Top 5 Things' (T5T) emails. Use when helping write, critique, or refine T5T emails, drafts with 'Top 5 Things' subject lines, or content for large NVIDIA distribution lists. Enforces critical formatting rules including proper 'Top 5 Things - [job area]' subject line format."
metadata:
  author: "Dave Farris <dfarris@nvidia.com>"
  tags:
    - t5t
    - top-5-things
    - email
    - communication
    - writing
    - nvidia-culture
  domain: communication
---

# Top 5 Things (T5T) Email Assistant

This skill helps NVIDIA employees write effective "Top 5 Things" emails sent to large distribution lists (1000+ people) that serve as NVIDIA's "global neural network" to detect opportunities, threats, alignment issues, and learnings.

## How to Use This Skill

### Step 1: Load Guidelines
Before helping with any T5T email, read `references/guidelines.md` for NVIDIA's T5T culture, Jensen's philosophy, format requirements, content principles, examples, and workflow checklists.

### Step 2: Determine the Task Type

Identify what the user needs:
- **Generate a draft from bullets** — turn brief notes into a polished T5T
- **Distill from verbose content** — condense long documents, meeting notes, or detailed writeups
- **Critique an existing draft** — provide specific feedback on what to improve
- **Refine a draft** — edit based on feedback while maintaining the user's voice
- **Generate from session history** — analyze recent Claude Code sessions and synthesize a T5T draft from the work activity

When critiquing, cite relevant principles from guidelines.md to support suggestions (e.g., "Jensen's golden rule: 'As much as needed, as little as possible' suggests this could be more concise"). Use citations for principle-based suggestions; basic grammar/clarity fixes don't need citations.

#### Session Analysis Workflow

Activates only for the "generate from session history" task type.

a. **Determine timeframe**: If the user specifies when they last sent a T5T, calculate `--since` hours from that date. Otherwise default to `--since 168` (one week).

b. **Compact scan**: Run the session analyzer in compact mode:
   ```bash
   python3 scripts/analyze_sessions.py --since <hours> --compact > /tmp/t5t_sessions_compact.json
   ```
   If the script fails or produces empty output (`[]`), tell the user no session data was found for that period and ask if they want to try a longer timeframe.

c. **Triage**: Skip trivial sessions where `user_message_count < 5` AND `files_changed` is empty AND `git_commits` is empty. If all sessions are trivial, tell the user and offer to fall back to a different task type (e.g., generate from bullets).

d. **Subagent batching** (when >3 non-trivial sessions): Launch up to 5 parallel subagents, each running `--session <id>` for full message detail. Each subagent should extract:
   - T5T-worthy signals (opportunities, threats, learnings, alignment issues)
   - Concrete metrics and outcomes
   - Collaboration points (who was involved, who should know)
   - Engagement hooks (what could someone act on or respond to)

   For ≤3 non-trivial sessions, skip subagents and read the full output directly.

e. **Synthesize into T5T items**:
   - Group related work across sessions into themes
   - Prioritize weak signals over pure status
   - Extract concrete metrics from session data
   - Identify collaborators for tagging
   - Apply reframe pattern (problems → completed analyses)

f. **Feed into iterative refinement** (Step 3 below) — the draft still needs human context. The user knows things the sessions don't capture (stakeholder reactions, strategic importance, upcoming deadlines).

#### Code Contribution Gathering

After session analysis (or at the start for non-session workflows), check for `glab` or `gh` CLI and pull recent code contributions. This adds concrete MR/PR references, reviewer names, and contribution context that session history alone misses.

a. **Detect CLI**: Check if `glab` (GitLab) or `gh` (GitHub) is available.

b. **Pull authored MRs/PRs**: Query for MRs/PRs authored by the user in the relevant timeframe. Use repos identified from session data (project directories, git remotes) or ask the user which repos to check.
   ```bash
   glab mr list --author=<username> --all --per-page=20 --repo="<group/project>"
   gh pr list --author=<username> --state=all --limit=20
   ```

c. **Pull reviews given**: Query for MRs/PRs where the user was a reviewer. Reviews show community engagement and cross-team collaboration.
   ```bash
   glab mr list --reviewer=<username> --all --per-page=20 --repo="<group/project>"
   ```

d. **Get details**: For relevant MRs/PRs, pull status (open/merged), reviewers, and comment counts. For reviews given, pull the user's comments to understand the nature of the review.

e. **Integrate into draft**: MR/PR numbers, reviewer @-mentions, and review activity are natural engagement hooks. They show concrete output and collaboration.

#### Source Material Collection

Session history captures *what you did* but not *why it matters*. After presenting session-derived themes, ask the user:

- "Do you have proposals, docs, or slides I should read for any of these items?"
- "Any presentations or talks you gave recently that relate to this work?"
- "Any data tables or benchmark results to reference?"

Paste or file references give the strategic framing and specific numbers that sessions alone miss.

### Step 3: Follow Iterative Workflow

T5T creation is an **iterative, conversational process**. Rarely a one-shot activity—expect to refine through multiple rounds.

**Ask Clarifying Questions When Needed:**
If input is vague or missing key context, ask targeted questions about role, priorities, key collaborators, or urgency. Ask the most critical 1-2 questions first to avoid overwhelming users.

**Before drafting, identify the signal:**
- Ask: "What could leadership or peers act on here?"
- If input is pure status, probe for the underlying signal (opportunity, threat, learning, alignment issue)

**After first draft, run the relevant workflow checklist from guidelines.md** (Generating from Bullets, Distilling from Verbose Content, or Critiquing a Draft) to check for engagement quality, proper framing, and completeness.

**Per-item iterative refinement:**
After the first full draft, work through items one at a time with the user rather than trying to polish everything at once. For each item:
1. Ask what the **engagement angle** is — what should make someone reply?
2. Ask if the framing is right — too much detail? Too little? Wrong emphasis?
3. Rewrite based on feedback before moving to the next item.

This is more effective than iterating on the full draft because each item has its own audience and purpose.
**Invite Feedback:**
After providing a draft or critique, invite feedback ("What would you like to adjust? Too formal? Too long?"), offer alternatives if appropriate, and be ready for multiple rounds of edits.

### Step 4: AI Writing Cleaner Pass

Before final export, run the `/ai-writing-cleaner` skill on the draft. T5T format naturally avoids some AI patterns (it's terse and dense), but watch for:
- Em dash overuse (some are fine for T5T scannability, but don't stack them)
- "Not X, it's Y" constructions
- Inflated significance language ("groundbreaking," "transformative")
- Promotional filler ("for free," "game-changing")

### Step 5: Export

Once the user is satisfied, ALWAYS offer to create an HTML file for Outlook (never markdown). See "Exporting to Outlook" section below.

## Exporting to Outlook

Once the user is satisfied with their T5T draft, ALWAYS offer to generate an HTML file (never markdown).

**Offer**: "Would you like me to create an HTML file you can copy into Outlook? This will preserve all the formatting."

**When they agree:**
1. Use Write tool to create HTML file with: DOCTYPE, head (Calibri/Arial 11pt), body with formatted content
2. Name it `t5t-[topic]-[date].html` in working directory
3. Provide instructions: "Open the HTML file in your browser, select all (Cmd+A), copy (Cmd+C), and paste into Outlook. The formatting will be preserved."

Keep HTML simple - standard tags only (`<b>`, `<i>`, `<ol>`, `<ul>`, `<li>`). Outlook strips complex CSS.

## Resources

### scripts/analyze_sessions.py
Session JSONL analyzer. Reads ~/.claude/projects/ and extracts structured data
organized into topic segments. Segments split on time gaps (default 10min),
branch changes, or cwd changes.

- **Default mode**: Full output with messages per segment (can be several MB)
- **`--compact` mode**: Metadata only (~300KB)
- **`--session <id>`**: Filter to specific session — use in subagents
- **Always pipe to a file** (`> /tmp/output.json`) — large outputs get lost to buffering
