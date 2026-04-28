# T5T Guidelines and Principles

## Core Philosophy (Jensen Huang's Vision)

Jensen created T5Ts to serve as NVIDIA's "global neural network" - a system where employees act as sensors detecting opportunities, threats, alignment issues, and learnings across the company.

"We've turned NVIDIA into an Internet of Things. We have sensors all over. You're all sensors. Every one of you who writes a Top 5 Things is essentially a sensor."

### Why Jensen Reads These Daily

"I'm looking to detect the weak signals. It's easy to pick up the strong signals, but I want to intercept them when they are weak."

### Jensen's Golden Rules

- "As much as needed, as little as possible"
- "Don't optimize for completeness but rather engagement and action"
- "Top 5 Things you are doing, on your mind, of interest that might be opportunity or threat, or that you learned"
- "More frequent from more people, is better than exhaustive reports from just a few"

## Identifying Weak Signals

A weak signal is something the organization should know about before it becomes obvious. Ask:

- **Opportunity**: Could this benefit other teams or customers?
- **Threat**: Could this become a bigger problem if ignored?
- **Learning**: Did we discover something others would repeat or avoid?
- **Alignment issue**: Are teams working at cross-purposes?

**T5T-worthy vs. just status:**
- ❌ "Working on evaluation framework" (status)
- ✅ "Evaluation framework revealed [unexpected finding] — investigating [root cause]" (weak signal)

When helping users, probe: "What's the signal here that leadership or peers could act on?"

## What Success Looks Like

**Engagement is the win:** Questions, collaboration offers, replies, and discussions indicate the T5T surfaced something valuable. This builds partnerships and ensures alignment.

### What Drives Engagement

T5T replies tend to be congratulatory or collaborative. Content that gets responses:

- **Milestones with numbers** — "[N] processed", "[X]% efficiency", "[N]x improvement". Easy to celebrate.
- **External validation** — Customer wins, press quotes, conference talks. Third-party proof invites "Congrats!"
- **Imminent releases** — "Launching Tuesday", "Paper out next week". Creates urgency.
- **Cross-team impact** — Work affecting multiple orgs gets more eyes and collaboration offers.

Content that gets silence (even if valuable):
- Pure problem statements without a path forward
- Process updates ("RFC in review") vs. outcomes
- Research insights without clear "so what"

## Reply Mechanics: Making It Easy to Respond

Engagement requires low friction. For each item, consider:

**Low-friction response types:**
- **Celebration**: Lead with a metric people can congratulate ("[X]% efficiency achieved")
- **Yes/no question**: "Does this approach align with your thinking?" beats "Thoughts?"
- **Specific expert ask**: "@name, you've solved this before — any pitfalls?" beats mass "feedback welcome"
- **Collaboration offer**: "Approach ready to share" invites requests

**High-friction (avoid):**
- Open-ended items with no clear response path
- Vague asks to 1000+ people ("let me know if interested")
- Passive language ("worth investigating" vs. "investigating this week — input welcome")

**Checklist for each item:**
- Is there something congratulatable?
- Is there a specific question or ask?
- Have I made it safe/easy to reply?

## Format Requirements

**Subject Line (CRITICAL!):** Must be "Top 5 Things - [Your job area]" - people filter on this exact format.

**Length:** ~200 words or less, scannable in 30 seconds.

**Number of items:** The "5" in "Top 5 Things" isn't rigid—use however many items fit your update while staying under ~200 words and scannable in 30 seconds.

**Tone:** Between professional and conversational. Not too formal, not too casual.

## Content Principles

### DO:
- **Lead with what matters most** — put important items at the top
- **Be specific and concrete** — use numbers, metrics, tangible outcomes
- **Tag collaborators who contributed or would benefit** — strategic tags invite engagement, mass-tagging dilutes it
- **Share learnings candidly** — both positive and negative findings (see "Reframe" section for how to frame negatives)
- **Flag risks and opportunities early** — surface weak signals
- **Include visuals directly** — charts, images (not links)
- **Use KISS principle** — keep it high-level, especially for complex technical findings. Questions from colleagues = engagement = win! T5Ts aren't the venue for comprehensive technical reports

### DON'T:
- **Oversell or be too subtle** — find the right balance, stay factual. LLMs can help draft T5Ts but keep tone natural
- **Write deep dives** — save detailed context for follow-ups
- **Rely on links for key info** — put the insight in the email; links are for optional deep-dives
- **Optimize for completeness** — optimize for engagement instead
- **Add too many caveats** — especially for research findings

## Sharing Negative Findings

Learnings are highly valued in NVIDIA culture. Share critical findings candidly to the full distribution list - this is how weak signals get detected early.

When sharing problems or failures:
- **Frame constructively** — lead with the learning, not just the problem
- **Be specific** — vague complaints don't help; provide actionable details
- **Link to tracking** — reference nvbugs or GitHub issues
- **Show the path forward** — what's being fixed, workarounds found
- **Balance the story** — celebrate what worked while being candid about challenges

### The Reframe: Problems → Opportunities

People engage with wins, not problems. Same information, different framing:

| Instead of... | Try... |
|---------------|--------|
| "X is broken" | "Completed analysis of X — clear fix identified" |
| "We found a limitation" | "Key learning: [insight]. Opens opportunity for [Y]" |
| "Y didn't work" | "Ruled out Y — validated Z as path forward" |

**Example:**
- ❌ "[System X] can't handle [use case Y] — [technical limitation]"
- ✅ "[Use case Y] audit complete: [N] issues identified for [improvement magnitude]"

Lead with what you *did* (audit, analysis, test), not what you *found wrong*.

## Requesting Help and Flagging Blockers

T5Ts are effective for surfacing resource needs and asking for assistance:
- Be clear about what's needed — "we need X to unblock Y"
- Distinguish urgency — FYI vs. blocker vs. critical
- Make it actionable — what decision or resource is needed?

## Structuring Ongoing Work

For ongoing initiatives, use: Goal → Status → Next steps

This helps readers quickly understand where things stand and how they might help.

**Tip:** Frame status as milestones when possible. "[N]% complete" gets less engagement than "Phase 1 complete — [milestone achieved]. Phase 2 ([next phase]) starting [timeframe]."

## Jensen-Praised Example
One engineer wrote a concise T5T that Jensen praised: "This was the way original Top 5 Things were done. Easy to read and understand."

Key elements from this example:
- Creative opening with personal touch
- Five crisp, concrete bullets
- Tangible outcomes (specific metrics)
- Easy to scan, no fluff
- Mix of completed and ongoing work

Note: This style works great for software dev but may not suit all roles. The principles matter more than format.

## Examples

### Example 1: Generating and Distilling

Whether starting from brief bullets or verbose content, the goal is the same: create a concise, scannable T5T with concrete details.

#### Input Option A: Brief Bullets
```
- finished scalability experiments
- found data pipeline bottleneck
- upgraded core component
- met with partner team
- working on new tooling
```

#### Input Option B: Verbose Content (~250 words)
```
Last week we ran a comprehensive set of experiments on our new approach. We
tested configurations across multiple scales and found that our approach
performs well up to a certain threshold, achieving [X]% efficiency which is
significantly better than the baseline approach which topped out at around
[Y]% efficiency. However, when we scaled beyond that threshold we started
seeing diminishing returns, likely due to [limiting factor].

On a separate note, while running these experiments we discovered an interesting
issue in our data pipeline. Processing is taking much longer than we expected -
about [N] times slower than our initial benchmarks suggested. After spending
time debugging, we traced it back to [root cause]. Someone from [partner team]
confirmed this is a known issue they've been meaning to address. We're working
on a fix now and should have it ready soon.

We also upgraded [core component] to the new version which adds support for
[new capability] and reduces [resource usage] by about [N]%. This should help
with [benefit].

Had a good meeting with [partner team]. They're planning to integrate our work
into their system in [timeframe]. One thing that came up - they mentioned
they're seeing some issues with [edge case] that we should probably investigate
on our end.

Finally, I've been refactoring [tooling] to support [new feature]. It's about
[N]% complete.
```

#### Generated T5T (~110-130 words)
```
Subject: Top 5 Things - [Your Job Area]

1. [Project] scales to [threshold] with [X]% efficiency (vs [Y]% baseline)
— validated across [range]. Beyond [threshold] we hit [limiting factor].
Approach ready to share.

2. Data pipeline bottleneck identified — processing [N]x slower than expected
due to [root cause]. Fix in progress with [partner team], ETA [timeframe].

3. [Component] upgrade deployed — adds [new capability], reduces [resource]
by [N]%, improves [benefit].

4. [Partner team] integration aligned for [timeframe] (@name @name) — they
flagged [edge case] worth investigating on our end.

5. [Tooling] refactor [N]% done — adding [new feature], completing [timeframe].
```

#### What Makes This Effective
- **Concrete metrics**: Specific numbers for efficiency, speed, percentages
- **Flags problems with timeline**: Issue identified, ETA provided
- **Tags collaborators**: @name references for relevant people
- **Invites engagement**: Open issue to investigate
- **Scannable**: 30 seconds to read
- **Removed filler**: "comprehensive set", "really interesting", "on a separate note"
- **Note:** This example has 5 items, but that's not required—use however many items make sense for your update

### Example 2: Critiquing a Draft

#### User's Draft
```
Subject: T5T -- [Job Area]

Working on new tooling this week. Also did some experiments. Met with
[partner team]. Upgrading some components. Found an issue in the pipeline.
```

#### Critique
```
Issues to fix:

1. **Subject line format** — Should be "Top 5 Things - [Your area]" not "T5T --"

2. **Too vague** — What experiments? What issue? What components? Add concrete details

3. **Buried lead** — If the pipeline issue is critical, lead with it

4. **Too terse** — Add context for 1000+ people, not just a personal to-do list

5. **No engagement hooks** — Tag collaborators, flag items "worth investigating", or note "approach ready to share"
```

### Example 3: Surfacing a Weak Signal (Research Finding)

**Input:**
"We tested whether technique X works for problem Y. It doesn't really.
Not sure if worth sharing."

**Generated T5T item:**
"Key learning: Technique X doesn't transfer to problem Y. X assumes [condition A]
but Y requires [condition B]. Best result was modest [N]% improvement at [N]x cost.
Implication: Y-specific approaches needed. @relevantteam, aligns with what
you're seeing?"

**Why this works:**
- Frames negative finding as "key learning"
- Explains *why* it didn't work (insight others can use)
- States the implication (what this means going forward)
- Specific question to relevant team

### Example 4: Engagement-Dead vs. Engaging (Research Context)

**Engagement-dead version:**
"Ran experiments on approach Z. Found some limitations. Working on next steps."

**Engaging version:**
"Key learning: Approach Z has limited visibility into [problem domain] —
it captures [surface signal] but misses [deeper signal]. Experiments showed
method A achieved [X]% success vs [Y]% for method B ([N]x improvement from
factors invisible to Z). Implication for roadmap: [domain] needs [capability]
beyond current approach. Exploring with @teamname."

**The difference:**
- "Key learning" not "found limitations"
- Quantified comparison ([X]% vs [Y]%)
- Explains the *why* (what's being missed)
- States roadmap implication
- Names the collaboration

## Workflow Checklists

### Generating from Bullets
1. Ask for role/job area if not provided
2. Identify most important/time-sensitive items
3. Add concrete metrics and outcomes
4. Tag relevant collaborators
5. Ensure proper subject line format
6. Check: any negatives reframed as opportunities?

### Distilling from Verbose Content
1. Identify key signals (learnings, risks, opportunities)
2. Extract concrete outcomes and metrics
3. Remove filler language
4. Reorder with most important items first
5. Keep only critical context
6. Reframe problems as completed analyses or identified opportunities

### Critiquing a Draft
1. Check subject line format
2. Evaluate clarity and specificity
3. Verify important items are at the top
4. Identify missing engagement hooks (tags, "ready to share", "worth investigating")
5. Assess length and scannability
6. Flag any problem-led framing that could be reframed
