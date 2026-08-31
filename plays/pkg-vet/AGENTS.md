# pkg-vet

## Purpose

Package vetting hero — before `npm install left-pad@2`, answer the question every developer asks anyway: is this package safe to adopt? One command returns a verdict (SAFE / CAUTION / AVOID) with reasons, per-source evidence, and a stage ledger.

**Target prize:** MacBook Pro (1st) — "The Play the field most wants to keep using"

## Ownership

- Author: playbookacademy
- Canonical URI: https://play.modiqo.ai/playbookacademy/pkg-vet@0.1.0
- Registry: public, released

## Local Contracts

- Entrypoint: `main.ts` (rote frontmatter DAG + TypeScript presentation)
- Resource: `resources/vet.py` (Python: registry fetch + OSV check + typosquat + scoring)
- Dependencies: `deps.toml` declares python3 >= 3.10
- No adapters, no auth, no browser — pure process.exec + public HTTPS (npm/PyPI/crates APIs + OSV)

## Work Guidance

- Frontmatter format: `/** @rote-frontmatter` then ` * ---` then YAML then ` * ---` then `*/` (BOTH fences required)
- metadata MUST include: rote_version, version, status, execution_model, flow_type, requires_endpoints, requires_sessions
- Resource files go under `resources/`, referenced as `@resource{filename}` in argv
- Step output accessed via: `step.outcome.output.body.stdout.text` (NOT step.stdout.text)
- Presentation body uses top-level await (NOT export default function)
- FlowOutput pattern: `const out = new FlowOutput()` then `out.human(str)`, `out.summary(str)`, `out.result(obj)` — do NOT return
- No f-strings in TypeScript presentation body (Deno runtime limitation)
- Lint gate: `rote play lint <name>` then `rote play release <name>` then `rote registry play push <path> playbookacademy`
- deps.toml format: `schema_version = 1` then `[[tools]]` with id/command/required/version_requirement, then `[[tools.install]]` with manager/package

## Verification

- `rote play lint pkg-vet` must pass before release
- `rote play run "https://play.modiqo.ai/playbookacademy/pkg-vet@0.1.0" packages=zod,react ecosystems=npm --yes` must produce verdicts
- Cold-pull rehearsal: run from a pristine directory with zero flags
- Every version bump must be a semver bump (immutable versions)
- Failure lanes: kill each source deliberately -> labeled unknowns, ledger honest, play completes

## Child DOX Index

No child docs needed — flat structure (main.ts + resources/).
