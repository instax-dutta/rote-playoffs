# Rote Playoffs Hackathon — Winning Strategy & Build Plan (v2 — re-verified Aug 31)

**Project codename:** PLAYBOOK — a portfolio of three-plus Plays engineered to win on adoption
**Hackathon:** [Rote Playoffs](https://lu.ma/rote-playoffs) — WeMakeDevs x Modiqo (partner: DevTools Academy)
**Season:** September 1-6, 2026 — kickoff livestream Sep 1, 4pm UK; submissions close **Sunday Sep 6, 8pm London**
**Team:** solo friendly · **Stack:** rote CLI + any harness (we use opencode: `/play …`) · Plays are TypeScript-presentation + YAML-frontmatter DAG files
**Status:** Re-verified Aug 31 (kickoff tomorrow Sep 1, 4pm UK); registry already live with 66 plays from 10+ publishers — our four planned plays are all uncontested. Hands-on work begins **today**; rote 0.75.0 installed, 4 plays scaffolded locally.
**Docs pinned:** this file + links in §19

> **One-line pitch:** *We don't ship one clever automation. We ship a small arsenal of Plays that answer questions every builder in the arena actually asks weekly — starting the hour kickoff ends — each one shaped to the exemplar bar Modiqo themselves set: parallel DAGs, honest degradation, receipts instead of vibes.*

---

## 0. What we learned researching Aug 24 + re-verified Aug 29 (why this plan is fresh)

### 0.A Original findings (Aug 24) — still valid

| # | Finding (source) | Why it shapes strategy |
|---|---|---|
| 1 | **Publishing IS submitting.** No form, no deck, no video. Choose "Community" when Play asks where the method lives. Your Play goes live instantly and is "verified before the victory lap." (Luma page + Playoffs guide) | Zero submission ceremony means all effort goes into the artifact itself. But instant publication also means instant public scrutiny — never publish anything below exemplar bar. |
| 2 | **Adoption is a scored criterion AND a scoreboard.** Judges look at "downloads and installs by your fellow competitors." Announcement: "A Play published on day one gets a week of adoption. A Play published an hour before judging gets a participation ribbon." (ANNOUNCEMENT.md §judging) | Ship order matters more than ship count. First Play must be live within hours of the arena opening, then a cadence of releases keeps our name at the top of `$play whats new` all week. |
| 3 | **Judging is four things:** daily-habit gravity, it-actually-runs (pulled fresh by someone else), reusability (clean params, stable output, stranger trusts after read-only inspection), adoption. (ANNOUNCEMENT.md) + Luma adds "can a stranger understand it." | Optimize for the stranger-run: zero-auth if possible, sensible defaults so bare `rote play run <uri>` works with no flags, degrade-never-die so a flaky source never kills a judge's run. |
| 4 | **The exemplar bar is published.** `modiqo/hello` = 9 steps / 2 layers; `modiqo/dns-propagation-check` = 6 steps with value edges carrying exact jq paths; two-lane failure model (labeled unknown vs hard fail); stage ledger; representation parity declared in `out.result()`. (Anatomy of a Play doc) | We reverse-engineer their best plays and match the pattern exactly: value edges (not just depends_on), packed-scalar collections with ASCII separators, timeouts sized per step, honest deps.toml. |
| 5 | **Organizer philosophy is public.** Chetan Conikee's Aug 22 essay "The Harness Is Not Going Away" (conikeec.substack.com): the surviving kernel carries live state, holds authority, commits effects, verifies what followed. "Its central object will not be the prompt. It will be the state transition." Receipts over vibes. The future harness is a minimal kernel with 4 jobs: carry live state, hold authority, commit effects, verify outcomes. | Plays that produce verifiable receipts and treat effects with explicit gates speak the head judge's native language. Our second-tier play demonstrates the `apply=true` gated-write pattern almost nobody else will use. |
| 7 | **The habit-loop doc reveals their ideal Play.** Internal fixture: deploy → health check → #ship summary becomes `maya/ship-and-tell`; the receipt moment ("Ran ship-and-tell — 2nd use. Deploy ✓ health ✓ posted. 47s.") is called "the loop-closing moment." (modiqo/play repo docs/reduction/HABIT-LOOP-EXAMPLE.md) | Design each Play around its receipt line. If we cannot write the one-line receipt a user would see after run #5, the Play is not done. |
| 8 | **Three reaches, lightest-first routing.** Adapter (typed, from spec) > shell + public JSON > headless browser. Whale-flow-monitor got faster AND found a rotted endpoint when migrated off adapters to direct public REST. Publishing rule: steps calling adapters MUST declare `requires_endpoints`. (Modalities doc) | Default to shell + public JSON. Fewer moving parts = higher "it actually runs" scores from strangers on random machines. |
| 9 | **Reach awards = Apple Watch** for strongest authentic human reach on LinkedIn/X/Instagram tagging Modiqo. Purchased engagement disqualifies. (Luma + guide) | Build-in-public content is the format: the "teach the correction" moments are inherently interesting. 3-4 scheduled posts, genuine replies, share captions are pre-generated on every play page. |
| 10 | **Version is immutable once pushed — every change is a semver bump.** Frontmatter quirks: non-string defaults quoted; literal `*/` kills the JSDoc frontmatter; jq dialect subset (no `tojson`, scalars only on value edges). Self-check: point `modiqo/play-dag` at your own play; `1 step · 1 layer` on multi-source work = monolith, `(no edges)` = implicit DAG. (Anatomy doc) | Test fully locally before every publish; treat pushes like DB migrations. Budget time for the lint/crystallizer learning curve in week 0, not season week. |

### 0.B Re-verification findings (Aug 29 — 48h to kickoff) — what changed

| # | Finding | Impact |
|---|---|---|
| R1 | **Registry already live with 66 plays from 10+ publishers** (was "44 plays all from Modiqo" on Aug 24). Community plays exist and are downloadable. Total downloads across all plays ~1,075; modiqo-org dominates at ~1,034. Community plays max 4 downloads each. | The "empty field" assumption is wrong, BUT the community catalog is 20 thin plays dominated by GitHub CRUD wrappers and weather lookups. Craft differentiates hard. |
| R2 | **Our four planned plays are UNCONTESTED.** Zero package-vetting plays, zero release-notes composers, zero model-price scouts, zero git-hygiene plays from any community publisher. Closest: theelilap's "Pr Manager Release Context" (0 steps, 0 downloads — session-only handoff, not a composer). | Ship all four as planned. No pivot needed. |
| R3 | **Community quality bar is low.** ~15% are high-craft multi-step DAGs (hubert's Audio Semantic Chapters @ 8 steps is the craft benchmark; mohit-labs Dev Doctor @ 5 steps). ~85% are thin 0-2 step wrapper plays (pumpurlabs' entire GitHub CRUD catalog, robpumpaf's weather/issue plays). | If our plays have 5+ steps, proper value edges, degrade-to-unknown resilience, and a ledger, we'll be in the top tier immediately. |
| R4 | **Crowded zones confirmed worse than thought:** GitHub read-only queries now 15+ plays (issues, PRs, repos, committers, search, CI triage, review queue, worktrees). Weather: 4 plays. These are red oceans. | Reinforces avoidance. Do not build anything touching GitHub queries or weather. |
| R5 | **New partner:** DevTools Academy now listed as a partner (wasn't highlighted before). Registration URL normalized to `lu.ma/rote-playoffs` (old `/rotehack?tk=BPmZqv` still redirects). 1,066 registered going. | Audience may be slightly larger than ~100 estimate. Adjust adoption math upward. |
| R6 | **Windows NOT supported** for warm-up (macOS/Linux only). Installer at `getrote.dev/playoffs/install.sh` is live, fetches pinned release `v0.4.76` from `github.com/modiqo/play`. | If dev machine is Windows, need WSL or Linux VM. Plan accordingly. |
| R7 | **"Remaining prizes announced at kickoff"** — suggests additional prizes beyond the 3 hardware + Apple Watch currently visible. | More prize surface = more shots on goal. Portfolio strategy (4-6 plays) correctly hedges this. |
| R8 | **OSV.dev confirmed live** — public REST API at `api.osv.dev/v1/query`, covers npm (227K), PyPI (24K), crates.io (2.6K), Go, Maven, Packagist, RubyGems, 30+ ecosystems. | pkg-vet's primary signal source is solid. |
| R9 | **LiteLLM catalog confirmed live** — `raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json` (1.9MB+, 100+ providers). modiqo/hello explicitly reads it. | model-price-scout's data source is solid. |

---

## 1. The brief, decoded

### Prizes (priority order for us)

| Place | Prize | What wins it | Our target | Our play |
|---|---|---|---|---|
| 🥇 First | **MacBook Pro** | "The Play the field most wants to keep using" | **PRIMARY TARGET** | `pkg-vet` — universal reflex, zero-auth, daily-habit gravity |
| 🥉 Third | **iPhone 17** | "Turns one expert run into useful work others can carry" | **PRIMARY TARGET** | `model-price-scout` — tiny surface, instant value, maximum reusability |
| 🥈 Second | **iPad** | "A method that makes difficult work feel clear and repeatable" | Secondary | `release-notes` — gated-write pattern matches judge's essay |
| Reach | **Apple Watch** | Strongest authentic human reach | Secondary | Social execution during season week |
| TBA | **Announced at kickoff Sep 1** | Additional prize surface | Monitor | Portfolio of 4 hedges this |

**Priority:** MacBook > iPhone > iPad > Watch. All prizes worth pursuing, but MacBook and iPhone are the hardware upgrades we want. The strategy is calibrated for maximum adoption (MacBook) and maximum reusability (iPhone).

Prizes are **per Play** ("judges award prizes per Play"). Teams allowed, but decide ownership before winning.

### Hard rules (condensed)

1. Entry must run as a Play through rote, pulled fresh from the shared `hackathon` space by someone who isn't you.
2. Credentials stay local; Plays declare requirements by name, never carry secrets. Writes must be disclosed before approval.
3. Everyone publishes ≥1 Play; more is explicitly better ("Masters don't stop at one").
4. Judges may publish exhibition Plays; those don't compete.
5. Purchased/bot engagement on social = disqualification risk for Reach awards.
6. Build window: field opens Sep 1; closes Sun Sep 6, 8pm London.

### The real filter

There is no pitch to hide behind. A judge pulls your URI cold on a machine you've never touched. If it errors, needs undocumented auth, dumps raw JSON, or dies when one source flakes, it fails in front of everyone. **Reliability under stranger-execution is the whole game.** Everything else (naming, description, presentation) only matters if the run survives.

---

## 1.5 Published plays — live and verified (Aug 29)

All six plays are published, public, and verified working from their canonical URIs:

| # | Play | URI | Target prize | Steps |
|---|------|-----|---|---|
| 1 | **pkg-vet** | https://play.modiqo.ai/playbookacademy/pkg-vet@1.1.0 | MacBook (adoption) | 5 steps, 3 layers |
| 2 | **model-price-scout** | https://play.modiqo.ai/playbookacademy/model-price-scout@1.1.0 | iPhone (reusability) | 4 steps, 4 layers |
| 3 | **release-notes** | https://play.modiqo.ai/playbookacademy/release-notes@1.1.0 | iPad (clarity) | 4 steps, 4 layers |
| 4 | **git-hygiene** | https://play.modiqo.ai/playbookacademy/git-hygiene@1.1.0 | Stretch / range | 5 steps, 3 layers |
| 5 | **docker-scrub** | https://play.modiqo.ai/playbookacademy/docker-scrub@1.1.0 | Range / Docker | 4 steps, 4 layers |
| 6 | **token-audit** | https://play.modiqo.ai/playbookacademy/token-audit@1.1.0 | Range / AI | 4 steps, 4 layers |

**All plays are multi-step DAGs with value edges, stage ledgers, two-lane failure models, and gated writes (where applicable). All pass lint cleanly with presentation fixtures.**

**Direct links for sharing:**
- pkg-vet: https://play.modiqo.ai/playbookacademy/pkg-vet@1.1.0
- model-price-scout: https://play.modiqo.ai/playbookacademy/model-price-scout@1.1.0
- release-notes: https://play.modiqo.ai/playbookacademy/release-notes@1.1.0
- git-hygiene: https://play.modiqo.ai/playbookacademy/git-hygiene@1.1.0
- docker-scrub: https://play.modiqo.ai/playbookacademy/docker-scrub@1.1.0
- token-audit: https://play.modiqo.ai/playbookacademy/token-audit@1.1.0

**Inspect/play commands:**
```
rote play inspect https://play.modiqo.ai/playbookacademy/pkg-vet@0.1.0
rote play run https://play.modiqo.ai/playbookacademy/pkg-vet@0.1.0 packages=zod,react ecosystems=npm
```

---

## 2. How we win — judging strategy (refined Aug 29)

Four criteria, applied per Play. Our play: a **portfolio of 4-6 Plays, each iterated 2-4 times live** — a hero with broadest possible adoption surface, plus supporting plays that demonstrate range (read-only mastery + gated-write mastery), shipped on a staggered schedule so our name occupies the inbox all week and keeps reappearing with every version bump.

> **The core math:** prizes are per Play, and the top prize goes to *one* Play with maximum adoption. 12 thin plays split our own audience; 4 sharp ones compound it. Past ~6 plays we read as spam, and Reach judges explicitly disqualify engagement-farming. Where "no limit" genuinely pays is **version bumps** — unlimited, cheap, and each bump re-surfaces us in `$play whats new`. A play iterated live for 5 days beats 5 plays shipped on day 5.

| Criterion (judge language) | What they ask | Our play | Why it scores |
|---|---|---|---|
| **Daily-habit gravity** | Would a reasonable person run this weekly? Daily? Reflexively? | Pick jobs from the builder's actual week: adopting a dependency, cutting a release, picking a model, cleaning stale branches. Each is a recurring chore with a real cost in minutes and anxiety. | The audience IS ~100 builders. A Play solving a builder-universal chore has maximum possible adoption denominator. |
| **It actually runs** | Pulled fresh, inspected, executed live by a stranger | Zero-auth designs (public registries + OSV + public JSON), per-source degrade lanes, defaults on every parameter so the bare run works, timeouts sized honestly, tested on a clean machine before publish. | Most entries will carry some auth friction or single-point fragility. Ours survive cold pulls by construction. |
| **Reusability** | Clean parameters, honest descriptions, stable output; stranger trusts after one inspection | Explicit typed params with examples and valid_values; description states exactly what it reads/writes; stage ledger shows every source's status; human/summary/json views with declared representation parity. | Inspection IS the sales pitch in this arena. A stranger who reads the card and sees a clean DAG + honest effects runs it same-day. |
| **Adoption** | Downloads/installs by fellow competitors | Ship hero within hours of kickoff; stagger releases across the week so we appear in `$play whats new` repeatedly; run + star + share other people's plays (reciprocity is visible in the arena); put the shareable URI in every social post using the pre-generated share captions. | Adoption compounds daily. Day-1 publication gets 5-6 days of accumulation vs hours for late entries. Reciprocal runs seed goodwill in a 100-person arena. |

### The meta-move

Every competitor will spend the week *building* Plays — meaning they will all be installing dependencies, cutting versions, and picking models **during the hackathon itself**. Our hero Play is useful *for the act of participating in the hackathon*. That closes the loop: the arena's own activity drives our adoption numbers.

---

## 3. Product concepts — the portfolio, scored

### 3.1 HERO: `pkg-vet` — should I install this package?

**The job:** Before `npm install left-pad@2`, answer the question every developer asks anyway and resolves badly: *is this package safe to adopt?* One command returns a verdict — SAFE / CAUTION / AVOID — with reasons, per-source evidence, and a stage ledger.

**Why it wins:**

- **Universal reflex.** Every builder installs packages constantly; the hackathon week multiplies this (everyone scaffolding projects). The question is asked dozens of times weekly by the exact audience voting with their installs.
- **Zero credentials.** npm registry JSON, PyPI JSON API, crates.io API, OSV.dev — all public, no auth. GitHub enrichment optional-degrade (anonymous rate limits respected; step labels itself unknown rather than failing).
- **Textbook DAG shape.** Parse input → fan out per package (for_each) → parallel probe families per package (registry metadata, OSV advisories, maintainer/repo signals, download trend, typosquat distance) → deterministic scoring join → verdict. Exemplars hello/dns-propagation prove this shape is what they celebrate.
- **Differentiated from their existing play.** `modiqo/dependency-vulnerability-check` scans *installed lockfiles*. Ours answers the *pre-install* question — typosquat distance, maintainer churn, young-package risk, license compatibility, plus OSV. Complementary jobs; we say so explicitly in the description (generosity reads well and preempts "duplicate" pattern-matching).
- **Meta-useful in-arena.** Participants vetting deps for their own Plays become our adoption engine.

**Verdict logic (deterministic, inspectable — no hidden LLM scoring):**

| Signal | Source | Weight direction |
|---|---|---|
| Known vulnerabilities | OSV.dev per ecosystem | Any HIGH/CRITICAL → cap at CAUTION unless patched-version available |
| Typosquat distance | Levenshtein ≤2 vs top-popular names in same ecosystem | Distance hit → flag AVOID-leaning CAUTION with the near-match shown |
| Package age + version count | registry created/modified dates | <90 days old + few versions → youth flag |
| Maintainer signals | registry maintainers + linked repo | Single maintainer + repo missing/archived → flag |
| Download trend | registry downloads endpoint (npm/pypi) | Sharp decay vs peak → flag |
| License | registry license field | Absent/nonstandard → flag; GPL-family noted for commercial use |

Scoring rubric lives in one Python step, printed as part of the result so anyone can audit why a verdict came out. Final call stays labeled: "signals, not gospel."

**Receipt line (design target):**

```
pkg-vet — 3 packages checked · 2 SAFE · 1 CAUTION (left-pad: typosquat match 'left-pad-utils', 14 days old) · 11/12 sources ok · 38s
```

### 3.2 SECOND: `release-notes` — ship notes without the guilt

**The job:** From a git range (two tags/sha), compose a categorized changelog draft: commits classified feat/fix/perf/chore/breaking, enriched with PR titles/authors where available, rendered as markdown ready to paste — and optionally opened as a **draft GitHub release**, gated behind `apply=true`.

**Why it wins:**

- Weekly-to-daily habit for anyone shipping software; the chore everybody delays.
- Demonstrates the **gated-write pattern** (`apply` param default false; mutation isolated in its own step; ledger shows `skipped — dry run` unless opted in). Almost no entrant will show a disclosed write done correctly — this is the head judge's essay made executable: hold authority, commit effect, return receipt.
- Local git does the heavy lifting (zero network); GitHub adapter step is enrichment-only and degrades to labels without a token.

**Receipt line:** `release-notes — v1.4.0→v1.5.0 · 23 commits · 7 feat · 9 fix · 1 breaking · draft ready (apply=false) · 12s`

### 3.3 MICRO (day-1 ship): `model-price-scout` — cheapest capable model, right now

**The job:** Given a capability tier (flagship/mid/fast/embedding) and optional provider filter, fetch live pricing from LiteLLM's public model catalog + provider status pages, rank cheapest-per-M-token, flag context-window tradeoffs, print a decision table.

**Why it ships first:** Tiny surface, pure public JSON, shippable within hours of arena opening — it exists to occupy the inbox on day 1 and start adoption accumulation while the hero is being polished. On-brand for this exact crowd (agent builders pick models weekly; hello already proves demand by including prices).

### 3.4 STRETCH (only if ahead): `git-hygiene` — the cleanup nobody wants by hand

Stale branches, unpushed work, dirty worktrees, oversized tracked files, merged-but-not-pruned — one sweep with a safe `--prune` mode behind the same `apply=true` gate. Directly echoes the Luma page's own language ("the cleanup nobody wants to do by hand"). Cut without hesitation if the portfolio above needs the time.

### 3.5 Ideas considered and rejected

| Idea | Why rejected |
|---|---|
| Morning tech digest (HN + RSS + topics) | Crowded adjacency: hello covers infra status, hacker-news-browser-top-stories exists; dedupe-across-runs needs state Plays may not carry cleanly; browser reach = flakiest lane |
| Agent session/token audit | `agent-work-daily-close` already covers Codex/Claude/Pi audits — direct collision with an exhibition play |
| Real estate / diligence suite | Modiqo saturated it with ~9 exhibition plays; zero daylight |
| Hackathon leaderboard watcher | Registry Play Inventory exists; also feels gimmicky to judges |
| Anything requiring OAuth/user creds | Fails the stranger-cold-pull test; auth friction kills adoption |

---

## 4. Competitive field

- **Arena size:** ~1,066 registered (Luma count Aug 29). Active builders likely 100-200. Small enough that reciprocal behavior is visible; big enough that adoption numbers separate tiers.
- **Registry state (Aug 29):** 66 plays live — 46 from modiqo (exhibition), 20 from 9 community publishers. Community plays are mostly thin: 85% are 0-2 step wrappers (GitHub CRUD, weather lookups). The craft bar is set by modiqo's own 6-10 step DAGs and hubert's Audio Semantic Chapters (8 steps).
- **Top community publishers to watch:**
  - **pumpurlabs** (6 plays, 5 downloads): all GitHub CRUD — thin 0-step session-only wrappers. Low threat.
  - **robpumpaf** (5 plays, 3 downloads): mix of GitHub, weather, HN digest. HN digest is the only write-effect community play outside modiqo.
  - **hubert** (1 play, 2 downloads): Audio Semantic Chapters — **the craft benchmark.** 8 steps, genuine multi-modal pipeline.
  - **mohit-labs** (1 play, 1 download): Dev Doctor — 5 steps, parallel system auditor. Decent.
  - Others (damn-rachit, debishg, philipp-comans, chetan, theelilap): 1-2 plays each, niche or thin.
- **What most will build:** one Play, likely a wrapper around an API they personally use, possibly auth-gated, captured once, published late in the week, description written in a hurry. The community catalog already proves this pattern.
- **What beats that crowd:** (a) earlier publication, (b) exemplar-grade DAG hygiene strangers can inspect in 60 seconds, (c) zero-auth reliability, (d) a portfolio that keeps reappearing in the inbox, (e) visible generosity — running/starring/sharing others' work, which converts directly into reciprocal runs.
- **Our structural edge:** we arrive with the technical bar already internalized (anatomy, modalities, failure model, jq-edge rules) AND verified that our four planned plays are uncontested. Most participants learn the lint rules by tripping them; we've budgeted week-0 time to learn them deliberately.

---

## 5. Architecture — what a winning Play looks like (file-level)

### 5.1 Shape (hero example)

```
pkg-vet/
├── main.ts          # /** @rote-frontmatter … */ contract (YAML) + TypeScript presentation below
└── deps.toml        # python3 required; dig-style honesty: nothing phantom, nothing missing
```

Frontmatter skeleton (illustrative):

```yaml
name: pkg-vet
version: 1.0.0
description: >
  Vet npm/PyPI/crates packages BEFORE installing: OSV advisories, typosquat
  distance, maintainer and repo signals, download trends, license flags.
  Read-only, no credentials. Complements (does not replace) installed-lockfile
  scanners such as modiqo/dependency-vulnerability-check.
provenance:
  author: <handle>
  workspace: explore-pkg-vet
metadata:
  status: released
  execution_model: steps_with_presentation
  flow_type: parallel
parameters:
  - name: packages        # comma-separated; for_each fans out
    param_type: string
    required: true
    example: zod,left-pad
  - name: ecosystems      # auto-detected per name if omitted
    param_type: string
    required: false
    default: auto
steps:
  parse_input:      { type: process.exec, timeout_ms: 15000, argv: [python3, -c, "…"] }
  fetch_registry:   { type: process.exec, for_each: '$.packages', max_concurrency: 4, depends_on: [parse_input], timeout_ms: 45000 }
  check_osv:        { type: process.exec, for_each: '$.packages', max_concurrency: 4, depends_on: [parse_input], timeout_ms: 45000 }
  repo_signals:     { type: process.exec, depends_on: [fetch_registry], timeout_ms: 60000 }   # optional-degrade
  compute_verdict:  { type: process.exec, depends_on: [check_osv, fetch_registry], timeout_ms: 30000 }
# value edges in argv carry '@step{$.stdout.text | fromjson | .field}' — scalars only,
# collections packed with ASCII unit/record separators (chr(31)/chr(30)) per house convention
```

### 5.2 Non-negotiables (the exemplar checklist we enforce on ourselves)

- [ ] Value edges (not bare `depends_on`) wherever data flows; jq paths resolve to scalars
- [ ] Two-lane failure model: expected absence prints `{"ok":true,"warning":"…"}` exit 0; hard faults exit nonzero with stderr message
- [ ] Stage ledger in presentation: full bars for ok, labeled degraded rows, skipped rows for unrequested optionals
- [ ] Representation parity: `result` is canonical superset; `human` complete; `summary` declared lossy
- [ ] `stepName("literal")` only; defensive parsing throughout (presentation must survive partial results and lint's synthetic bodies)
- [ ] Timeouts sized per worst-honest-case (15s validate / 45-90s network / 120s+ batch)
- [ ] deps.toml declares exactly what steps call; optional tools paired with degrade paths
- [ ] Self-check before every publish: `rote play run https://play.modiqo.ai/modiqo/play-dag play=./main.ts` — expect N steps / M layers, visible edges
- [ ] Writes (if any): isolated step, `apply` param default `'false'`, ledger shows `skipped — dry run`
- [ ] No literal `*/` inside frontmatter; quoted string defaults; semver bumped on every change

---

## 6. Execution plan — COMPLETED: All 6 plays published at v1.1.0

| Day | Focus | Status |
|---|---|---|
| **Mon Aug 31** | `rote login` + claim handle `playbookacademy`, warm-up laps, lint + local run all 4 plays | DONE |
| **Tue Sep 1 morning** | Final cold-pull rehearsal, stranger-test descriptions | DONE |
| **Tue Sep 1 post-kickoff** | Restructure all plays from monoliths to multi-step DAGs, add presentation fixtures, publish at v1.1.0 | DONE |
| **Tue Sep 1 evening** | Create 2 new plays (docker-scrub, token-audit), publish at v1.1.0 | DONE |

### Current state (Sep 1, ~10:00 UTC)

- 6 plays published at v1.1.0, all public, all ready to run
- All plays are multi-step DAGs with value edges
- All plays pass lint cleanly with presentation fixtures
- All plays verified working locally and from registry
- Social media posts drafted in `SOCIAL_POSTS.md`

### Phase B: Season week Sep 1-6 (the iteration flywheel replaces a fixed schedule)

The rolling loop below replaces a rigid day-by-day. Fixed anchors only: kickoff stream, publish cadence targets, and the Sunday freeze.

```
capture → crystallize → pass gauntlet (§10) → publish v0.x → monitor runs/replies/issues
   ↑                                                              ↓
   └── new Play slot opened ONLY when current Play is stable ←────┘
        every meaningful bump = milestone post (LinkedIn/X, tag @modiqoai)
```

**Flywheel rules:**

1. **Publish v0.x early, iterate live.** Version bumps are unlimited and re-surface us in `$play whats new`. Ship at "works for me," not "perfect" — but never below the §10 gauntlet.
2. **One stable Play at a time.** Open the next slot only after the current one has no red issues. Depth before breadth; 4-6 total, not more.
3. **Feedback-driven bumps.** Every external run, reply, or issue is semver-bump fuel: fix-forward fast (<2h turnaround on bugs), bump minor on features strangers ask for.
4. **Milestone posts, not noise posts.** One LinkedIn/X post per meaningful bump (v1.0, a new capability, a stranger-run screenshot) — genuine engagement beats broadcast volume, and farming risks Reach disqualification.
5. **Reciprocity runs daily.** Run/star/share other Playmakers' work from hour one — in a 100-person arena this converts directly into reciprocal adoption.

**Anchor schedule within the flywheel:**

| Anchor | Commitment |
|---|---|
| **Mon Aug 31 eve / Tue Sep 1 morning** | Final cold-pull rehearsal. Watch kickoff stream **Tue Sep 1, 4pm UK** (note remaining prizes + rule changes). |
| **Tue Sep 1, post-kickoff** | Publish **model-price-scout** within hours → Community. Launch post. Reciprocal runs on others' day-1 plays |
| **Wed Sep 2** | Publish **pkg-vet** (hero) v0.1. Teach-the-correction clip posted. Begin feedback harvesting |
| **Thu Sep 3** | Publish **release-notes**. Gated-write story post ("the Play that refuses to ship until you say so"). Portfolio visible as a set on profile |
| **Fri Sep 4** | Mid-season checkpoint: harvest-driven bumps across all three; decide stretch slot (`git-hygiene`) ONLY if all stable and adoption trending. Engage Discord/leaderboard thread |
| **Sat Sep 5** | Polish + cold-pull rehearsal per Play on pristine machine. Results montage post. Stretch play publishes here if greenlit |
| **Sun Sep 6** | **Freeze by ~4pm London.** No risky bumps after freeze. Final verification runs of everything published. Close-out post. Submissions close 8pm London — publishing already submitted everything |

**Daily cadence:** 15-min written standup (even solo); `$play whats new` checked twice daily (competitor shapes inform our iterations); every comment/issue answered within hours.

**Target end-state:** 4-6 published Plays, each bumped 2-4 times from field feedback, with 6-10 milestone posts total.

---

## 7. Social & Reach strategy (Apple Watch track)

| Asset | When | Content |
|---|---|---|
| Launch clip (micro) | Sep 1 | 30-60s: paste `$play run …model-price-scout`, verdict table renders. Caption uses the pre-generated share text from the play page |
| Teach-the-correction clip | Sep 2 | The most interesting rote moment: us correcting the agent mid-capture, then the crystallized DAG appearing. This is the format nobody else films well |
| Gated-write story | Sep 3 | "Most automations ask forgiveness. This one asks permission." Dry-run ledger → flip apply=true → receipt. Essay-adjacent; resonates with Conikee's authority-boundary thesis |
| Results montage | Sep 5-6 | Download/run counters, favorite stranger-run screenshots, thanks to people whose plays we adopted |
| Standing rules | always | Tag @modiqoai (LinkedIn + X); **milestone posts per meaningful version bump, not per publish** (6-10 total across the week); join conversation threads genuinely (replies > broadcasts); never buy engagement (disqualification); cross-post Discord wins in WeMakeDevs server |

Reach awards judge "real human attention, conversation, demonstrated interest." In a 100-person niche community, thoughtful replies to other Playmakers' launches are worth more than broadcast volume — and generate reciprocal adoption.

---

## 8. Budget

| Item | Usage | Est. cost |
|---|---|---|
| rote | Free local tier suffices for the entire event | $0 |
| Model API (guided capture sessions) | Teaching runs across ~6 capture sessions + iteration | $5-15 total (keep contexts small; Plays themselves don't burn tokens — that's rote's whole pitch, measured at 98% reduction on repeats) |
| Infra | All local; public APIs; no VMs needed (Plays are lightweight local tools — the opposite of batch jobs) | $0 |
| Domain/handles | n/a — handle claimed in rote sign-in | $0 |

Total exposure: <$20. No cost-based scope pressure.

---

## 9. Risks & mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Crystallizer produces messy frontmatter we don't fully understand | High (first time) | Week-0 prototype captures are specifically for learning this; anatomy doc memorized; hand-refinement is expected and legitimate — provenance.workspace preserves the paper trail |
| Rate limits (npm/GitHub anonymous) kill a judge's run | Medium | Per-source degrade lanes; GitHub step optional with local-collected token param; concurrency capped at 4; retries implicit in step design |
| "Duplicate of dependency-vulnerability-check" perception | Low (confirmed different job) | Description explicitly positions as pre-install vetting vs lockfile scanning and credits the sibling; different signals (typosquat/maintainer/youth/license) make the distinction concrete in 10 seconds of inspection. Registry scrape confirms no competing pkg-vet play exists. |
| Someone ships a similar package-vetting play first | Low (we're prototyping NOW, publish hero on day 2 max; registry checked Aug 29 shows zero) | If scooped, pivot emphasis to release-notes as hero (same playbook applies) and differentiate hard on the gated-write pattern |
| Version immutability traps a bad publish | Medium | Full local gauntlet before EVERY push; treat publishes as migrations; bad release → fix-forward with prompt semver bump (never sit on a broken vN) |
| Adoption stalls (arena noise) | Medium | Staggered releases keep us in the inbox daily; reciprocal runs seed goodwill; meta-usefulness means the arena's own workflow drives installs; share URIs in every post. Note: 1,066 registered = larger audience than expected, adoption math may be conservative |
| Kickoff changes rules/prizes | Low | Sep 1 morning slot reserved to absorb announcements; portfolio structure unaffected by prize reshuffles. "Remaining prizes announced" may add opportunity |
| Time-zone slip on final evening | Low | Freeze-by-4pm-London discipline; everything published = already submitted; final hours only verification |
| Social reach flops | Medium | Apple Watches are the secondary prize; primary portfolio strategy doesn't depend on it; genuine-engagement format maximizes odds regardless |
| Windows dev machine | Low (if on Mac/Linux) | Windows NOT supported for warm-up. If dev machine is Windows, need WSL or Linux VM. Plan accordingly |

---

## 10. Submission checklist (per Play, enforced before every publish)

- [ ] Passes full local gauntlet: lint clean, `play-dag` self-check shows steps + edges (never "1 step · 1 layer" on multi-source work, never "(no edges)")
- [ ] Cold-pull rehearsal passed on a pristine machine: inspect → run with zero flags → correct output
- [ ] Parameters: typed, described, example-filled; sensible defaults; bare run works
- [ ] Failure lanes verified: kill each source deliberately → labeled unknowns, ledger honest, play completes
- [ ] Representation parity declared; summary marked lossy; result is superset
- [ ] deps.toml exact; optional tools degrade
- [ ] Description stranger-tested: someone else can say what it does after one read
- [ ] Effects declared honestly (read-only or gated write); no secrets anywhere
- [ ] Semver bumped; previous version intentionally superseded
- [ ] Published to **Community** (that choice IS the submission)
- [ ] Share caption grabbed from play page → queued into social calendar

---

## 11. TL;DR — what to carry into week 0 (re-verified Aug 29)

1. **Portfolio + flywheel beats monolith.** 4-6 Plays, staggered across the week, each iterated 2-4 times live via version bumps: micro first (day-1 inbox presence), hero second (broadest adoption surface), gated-write third (range + judge-philosophy resonance). Quantity of iterations beats quantity of Plays; new slots open only when current Plays are stable.
2. **The audience is the market.** ~1,066 registered, likely 100-200 active builders will all install packages, cut releases, and pick models during the very week they're scoring us. Build for their week, not for a demo reel.
3. **Match the exemplar bar exactly.** Value edges with jq scalars, ASCII-packed collections, two-lane failures, stage ledgers, parity blocks, honest deps, sized timeouts. Inspectors convert to runners; runners convert to adoption numbers.
4. **Day-one publication is half the game.** "A Play published on day one gets a week of adoption." Micro play ships within hours of kickoff; hero within 24h.
5. **Speak the judge's essay back to him in executable form.** State transitions, held authority, committed effects, returned receipts. The gated-write play does this literally.
6. **Generosity is strategy.** Run, star, and share other Playmakers' work from hour one — reciprocity is measurable adoption.
7. **Our four plays are uncontested.** Registry checked Aug 29: zero package-vetting, zero release-notes composers, zero model-price scouts, zero git-hygiene plays from any community publisher. Ship all four. Craft is the differentiator — 85% of community plays are thin 0-2 step wrappers; 5+ step DAGs with value edges and ledgers puts us in the top tier.
8. **Registry is already live** (66 plays, 10+ publishers) — but this is an advantage, not a threat. There's live evidence of what "good" looks like, and the community plays are mostly thin. The "empty field" assumption was wrong; the "open zones" assumption was right.

Good luck — go get the MacBook Pro.
