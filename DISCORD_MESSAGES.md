# Discord Messages for Rote Playoffs

## Message 1: pkg-vet (Hero Play)

**pkg-vet — should I install this package?**

Before `npm install left-pad@2`, get a verdict. One command returns SAFE / CAUTION / AVOID with reasons, per-source evidence, and a stage ledger.

What it catches:
→ Known vulnerabilities (OSV.dev per ecosystem)
→ Typosquat distance (Levenshtein ≤2 vs popular names)
→ Young packages (<90 days old)
→ Few versions (<3 published)
→ Missing/nonstandard licenses

Zero credentials. Read-only. Degrades gracefully when sources flake.

Try it:
```
rote play run https://play.modiqo.ai/playbookacademy/pkg-vet@1.1.0 packages=zod,left-pad ecosystems=npm
```

Play: https://play.modiqo.ai/playbookacademy/pkg-vet@1.1.0

---

## Message 2: model-price-scout (Micro Play)

**model-price-scout — cheapest capable model, right now**

Picking an AI model for a new project? Fetches live pricing from LiteLLM's public catalog, ranks cheapest-per-Minput-token by tier (flagship / mid / fast / embedding), flags context-window tradeoffs, prints a decision table.

Zero credentials. Pure public JSON.

Try it:
```
rote play run https://play.modiqo.ai/playbookacademy/model-price-scout@1.1.0 tier=mid providers=all max_results=10
```

Play: https://play.modiqo.ai/playbookacademy/model-price-scout@1.1.0

---

## Message 3: release-notes (Gated-Write Play)

**release-notes — ship notes without the guilt**

From a git range (two tags/SHAs), composes a categorized changelog draft: commits classified feat/fix/perf/chore/breaking, enriched with authors, rendered as markdown ready to paste.

Dry-run by default. Set `apply=true` to create the release. Until then, read-only.

The Play that asks permission instead of forgiveness.

Try it:
```
rote play run https://play.modiqo.ai/playbookacademy/release-notes@1.1.0 from_ref=HEAD~10 to_ref=HEAD
```

Play: https://play.modiqo.ai/playbookacademy/release-notes@1.1.0

---

## Message 4: git-hygiene

**git-hygiene — the cleanup nobody wants by hand**

Stale branches, unpushed work, dirty worktrees, merged-but-not-pruned branches — one sweep with a safe `--prune` mode behind `apply=true`.

Try it:
```
rote play run https://play.modiqo.ai/playbookacademy/git-hygiene@1.1.0 repo_path=.
```

Play: https://play.modiqo.ai/playbookacademy/git-hygiene@1.1.0

---

## Message 5: docker-scrub

**docker-scrub — reclaim Docker disk space safely**

Scans for dangling images, unused volumes, and build cache. Computes a cleanup plan. Dry-run by default, `apply=true` to execute.

Try it:
```
rote play run https://play.modiqo.ai/playbookacademy/docker-scrub@1.1.0
```

Play: https://play.modiqo.ai/playbookacademy/docker-scrub@1.1.0

---

## Message 6: token-audit

**token-audit — AI prompt bloat + API cost projector**

Scans a directory for prompt files, estimates token counts, flags bloat (>4k tokens), and projects daily API costs across 5 models (GPT-4o, Claude 3.5 Sonnet, etc.).

Try it:
```
rote play run https://play.modiqo.ai/playbookacademy/token-audit@1.1.0 dir=.
```

Play: https://play.modiqo.ai/playbookacademy/token-audit@1.1.0

---

## Combined Message (All 6 Plays)

**playbookacademy — 6 Plays for the Rote Playoffs**

Every Play is a multi-step DAG with value edges, stage ledgers, and cold-pull reliability. Zero credentials, no auth friction.

1. **pkg-vet** — should I install this package? (OSV, typosquat, age, license)
2. **model-price-scout** — cheapest capable AI model, right now
3. **release-notes** — ship notes without the guilt (gated write)
4. **git-hygiene** — the cleanup nobody wants by hand
5. **docker-scrub** — reclaim Docker disk space safely
6. **token-audit** — AI prompt bloat + API cost projector

All public, all ready to run:
https://play.modiqo.ai/playbookacademy/pkg-vet@1.1.0
https://play.modiqo.ai/playbookacademy/model-price-scout@1.1.0
https://play.modiqo.ai/playbookacademy/release-notes@1.1.0
https://play.modiqo.ai/playbookacademy/git-hygiene@1.1.0
https://play.modiqo.ai/playbookacademy/docker-scrub@1.1.0
https://play.modiqo.ai/playbookacademy/token-audit@1.1.0

---

## Short-form (for quick shares)

**pkg-vet** — should I install this package? OSV vulns, typosquat, age, license. One command, zero credentials.
```
rote play run https://play.modiqo.ai/playbookacademy/pkg-vet@1.1.0 packages=zod,left-pad
```
https://play.modiqo.ai/playbookacademy/pkg-vet@1.1.0
