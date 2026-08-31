# git-hygiene

## Purpose

Git cleanup audit — stale branches, unpushed work, dirty worktrees, oversized tracked files, merged-but-not-pruned branches — one sweep with a safe `--prune` mode behind the same `apply=true` gate.

**Target prize:** Stretch / range demonstration (not primary target)

## Ownership

- Author: playbookacademy
- Canonical URI: https://play.modiqo.ai/playbookacademy/git-hygiene@0.1.0
- Registry: public, released

## Local Contracts

- Entrypoint: `main.ts` (rote frontmatter DAG + TypeScript presentation)
- Resource: `resources/hygiene.py` (Python: git branch/worktree/file analysis)
- Dependencies: `deps.toml` declares python3 >= 3.10
- No adapters, no auth, no browser — pure process.exec + local git binary

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
- Gated-write pattern: `apply` param default `'false'`, mutation isolated in its own step, ledger shows `skipped — dry run` unless opted in

## Verification

- `rote play lint git-hygiene` must pass before release
- `rote play run "https://play.modiqo.ai/playbookacademy/git-hygiene@0.1.0" repo_path=<git-repo> --yes` must produce an audit report
- Cold-pull rehearsal: run from a pristine directory with zero flags
- Every version bump must be a semver bump (immutable versions)
- apply=true path must be tested on a throwaway repo (prunes merged branches)

## Child DOX Index

No child docs needed — flat structure (main.ts + resources/).
