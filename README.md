# Rote Playoffs — PlaybookAcademy

7 multi-step DAG Plays for the [Rote Playoffs](https://luma.com/rotehack) hackathon. Zero credentials, cold-pull ready.

## Plays

| # | Play | Verdict | Steps | Install |
|---|------|---------|-------|---------|
| 1 | **pkg-vet** | should I install this package? | 5 steps, 3 layers | `rote play run https://play.modiqo.ai/playbookacademy/pkg-vet@1.2.0 packages=zod,left-pad` |
| 2 | **model-price-scout** | cheapest capable AI model, right now | 4 steps, 4 layers | `rote play run https://play.modiqo.ai/playbookacademy/model-price-scout@1.2.0 tier=mid` |
| 3 | **release-notes** | ship notes without the guilt | 4 steps, 4 layers | `rote play run https://play.modiqo.ai/playbookacademy/release-notes@1.2.0 from_ref=HEAD~10 to_ref=HEAD` |
| 4 | **git-hygiene** | the cleanup nobody wants by hand | 5 steps, 3 layers | `rote play run https://play.modiqo.ai/playbookacademy/git-hygiene@1.2.0 repo_path=.` |
| 5 | **docker-scrub** | reclaim Docker disk space safely | 4 steps, 4 layers | `rote play run https://play.modiqo.ai/playbookacademy/docker-scrub@1.2.0` |
| 6 | **token-audit** | AI prompt bloat + API cost projector | 4 steps, 4 layers | `rote play run https://play.modiqo.ai/playbookacademy/token-audit@1.2.0 dir=.` |
| 7 | **auth-scan** | auth security audit for Express/Node.js | 5 steps, 3 layers | `rote play run https://play.modiqo.ai/playbookacademy/auth-scan@1.1.0 src=./backend/src` |

## Design principles

- **Multi-step DAGs** — every Play has 4-5 steps with value edges (jq scalars), not single-step monoliths
- **Stage ledgers** — human output shows which steps completed vs degraded
- **Two-lane failure** — expected absence exits 0 with a warning; hard faults exit nonzero
- **Gated writes** — mutation only behind `apply=true`; dry-run by default
- **Cold-pull ready** — no hardcoded paths, no auth friction, works on a fresh machine

## Structure

```
plays/
  pkg-vet/              # Package vetting hero (MacBook target)
  model-price-scout/    # LiteLLM pricing scout (iPhone target)
  release-notes/        # Changelog composer with gated-write (iPad target)
  git-hygiene/          # Git cleanup audit (stretch/range)
  docker-scrub/         # Docker disk cleanup
  token-audit/          # AI token budget auditor
  auth-scan/            # Auth security audit for Express/Node.js
```

Each play is a self-contained package: `main.ts` + `resources/` + `deps.toml`.

## Links

- **Registry:** https://play.modiqo.ai/playbookacademy
- **Season:** Sep 1-6, 2026
- **Prizes:** MacBook Pro (1st), iPad (2nd), iPhone 17 (3rd), Apple Watch (Reach)
