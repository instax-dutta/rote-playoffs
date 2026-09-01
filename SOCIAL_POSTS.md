# Social Media Posts for Rote Playoffs

## Post 1: Launch Announcement (LinkedIn + X)

**Option A (Launch focus):**

We just published 6 Plays for the Rote Playoffs hackathon. Each one solves a real builder chore that eats time every week.

The lineup:
- pkg-vet: should I install this package? (OSV vulns, typosquat, age, license)
- model-price-scout: cheapest capable AI model, right now
- release-notes: ship notes without the guilt (gated write)
- git-hygiene: the cleanup nobody wants by hand
- docker-scrub: reclaim Docker disk space safely
- token-audit: AI prompt bloat + API cost projector

Every Play is a multi-step DAG with value edges, stage ledges, and gated writes. No hardcoded paths, no auth friction. Pull cold, run clean.

Try them: https://play.modiqo.ai/playbookacademy/pkg-vet@1.1.0

@modiqoai #RotePlayoffs #PlaybookAcademy

---

**Option B (Technical depth):**

Why most hackathon Plays fail the cold pull: hardcoded paths, single-step monoliths, auth friction.

We restructured all 6 of our Plays to match the exemplar bar modiqo set:
- Multi-step DAGs with value edges (jq scalars)
- Stage ledgers in human output
- Two-lane failure models (degrade, never die)
- Gated writes behind apply=true

pkg-vet went from 1 step to 5 steps, 3 layers. It now parses input, fans out to parallel probes (registry, OSV, typosquat), then joins into a deterministic verdict.

Pull it cold: https://play.modiqo.ai/playbookacademy/pkg-vet@1.1.0

@modiqoai #RotePlayoffs

---

## Post 2: Teach-the-Correction (Sep 2-3)

**LinkedIn:**

The most interesting rote moment this week: us correcting the agent mid-capture, then watching the crystallized DAG appear.

Turns out the LiteLLM catalog is 1.9MB. Too big to pass as a CLI argv argument. So we switched to a temp-file pattern: fetch writes to disk, downstream steps read file paths through value edges.

Small detail. But it's the difference between "works on my machine" and "works on the judge's machine."

@modiqoai #RotePlayoffs

---

## Post 3: Gated-Write Story (Sep 3-4)

**LinkedIn:**

Most automations ask forgiveness. This Play asks permission.

release-notes composes your changelog, renders the markdown, shows you the dry-run ledger. Then it stops.

Set apply=true and it creates the release. Until then, it's read-only.

The head judge's essay: "hold authority, commit effects, return receipt." We made it executable.

Try it: https://play.modiqo.ai/playbookacademy/release-notes@1.1.0

@modiqoai #RotePlayoffs

---

## Post 4: Results Montage (Sep 5-6)

**LinkedIn:**

6 days. 6 Plays. All multi-step DAGs. All passing cold pull.

Stats:
- pkg-vet: 5 steps, 3 layers, 3 parallel probe families
- model-price-scout: 4 steps, file-based data passing for 1.9MB catalog
- release-notes: 4 steps, gated write pattern
- git-hygiene: 5 steps, 3 parallel scanners
- docker-scrub: 4 steps, gated cleanup
- token-audit: 4 steps, cost projection across 5 models

Thanks to everyone who ran, starred, and shared. GG.

@modiqoai #RotePlayoffs

---

## Pre-generated Share Captions (for each play)

**pkg-vet:**
Just ran pkg-vet on a suspicious package. Got a verdict in 38s: typosquat match, 14 days old, 1 HIGH advisory. Saved me from installing malware. https://play.modiqo.ai/playbookacademy/pkg-vet@1.1.0 @modiqoai #RotePlayoffs

**model-price-scout:**
Picking an AI model for a new project? model-price-scout fetched live pricing from LiteLLM, ranked cheapest-per-Mtok by tier, flagged context tradeoffs. 5 seconds to a decision table. https://play.modiqo.ai/playbookacademy/model-price-scout@1.1.0 @modiqoai #RotePlayoffs

**release-notes:**
Spending 20 minutes every release writing changelog notes? release-notes composes categorized changelog drafts from git ranges. Dry-run by default, apply=true to ship. https://play.modiqo.ai/playbookacademy/release-notes@1.1.0 @modiqoai #RotePlayoffs

**git-hygiene:**
Found 3 stale branches and 2 merged-but-not-pruned branches in my repo. git-hygiene audits in one sweep, safe prune behind apply=true. https://play.modiqo.ai/playbookacademy/git-hygiene@1.1.0 @modiqoai #RotePlayoffs

**docker-scrub:**
Docker was eating 15GB of disk. docker-scrub scanned, identified reclaimable space (dangling images, unused volumes, build cache), and cleaned up behind apply=true. https://play.modiqo.ai/playbookacademy/docker-scrub@1.1.0 @modiqoai #RotePlayoffs

**token-audit:**
Found a 9000-token prompt file in my repo. token-audit scanned all prompts, flagged bloat, projected API costs across 5 models. $75/day for claude-3-5-sonnet at 1000 runs. https://play.modiqo.ai/playbookacademy/token-audit@1.1.0 @modiqoai #RotePlayoffs
