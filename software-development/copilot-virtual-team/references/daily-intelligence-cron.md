# Daily Intelligence Briefing Cron

Set up a recurring cron job that reads repo documentation + live data and delivers one sharp, current, actionable thought each day. Complements the virtual Copilot team — the team provides on-demand depth, the cron provides automated breadth.

## When to use

- The user wants a daily pulse on their domain without having to ask
- They have a repo with decision records, policies, and frameworks
- They want proactive intelligence, not reactive reporting

## Configuration

```
name: "Daily Platform Thinking"
schedule: "0 7 * * *"         # 07:00 daily
deliver: origin                # sends to the current chat
enabled_toolsets: [file, web, terminal]
```

## What the cron does

1. Reads the repo — looks at recently modified docs, ADRs, escalations, roadmap. Checks the last few commits for new decisions.
2. Checks live data — observability snapshots, health metrics, cost data (whatever's available in the environment).
3. Synthesises one specific, current, actionable thought — not generic, not a newsletter.
4. Delivers it directly to the user.

## Prompt pattern

```
You are {role}'s daily thinking assistant. Produce ONE sharp, current, actionable thought.

## Your task
1. Read the repo at {path} — especially the roadmap, recent ADRs, escalations, recently modified docs
2. Check live data at {path} for current health
3. Think about ONE thing worth attention today

## What a thinking item looks like
- A pattern emerging from recent decisions
- A risk forming (cost creep, policy gap, tech debt)
- An opportunity to unblock a team
- A framework gap worth addressing
- Something from live data worth investigating

## Format
🚀 **Today's Thinking Item: {short title}**

**What it is:** 2-3 sentences.

**Why it matters today:** Connection to roadmap, capacity, or specific needs.

**One action if relevant:** Single specific action, or "Just awareness — no action needed."

**Source:** Which doc, metric, or pattern.
```

## What makes a good thinking item

| Good | Not good |
|------|----------|
| "Three workloads landed this week without ops policies enforced" | "The weather is sunny" |
| "Current burn rate will exhaust budget by 15th — act now" | "Here's a history of cloud computing" |
| "ADR-003 chose Cosmos DB but we now have 5 Cosmos accounts — revisit" | "Cloud is important" |

## Pitfalls

- **Generic drift:** Without explicit instructions to be current and specific, the cron will default to generic observations. The prompt must emphasise "current, specific, one thing."
- **Stale repo:** If the repo hasn't changed in weeks, the cron will produce forced observations. Add explicit instruction: "If nothing has changed, say so rather than invent."
- **No live data fallback:** If observability data is unavailable, the cron should still work from repo content alone. Don't make it dependent on a specific file path.
- **07:00 delivery:** The user may be asleep or commuting. Keep the item short enough to scan in under 30 seconds.
