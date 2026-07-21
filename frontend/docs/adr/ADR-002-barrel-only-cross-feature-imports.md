# ADR-002: Barrel-Only Cross-Feature Imports

**Status:** Accepted
**Date:** 2026-07-21

## Context

Product Architecture §23 states that `features/experiments` and
`features/runs` "should never import each other's internals, only shared
`components/ui` primitives and `lib/api-client`." Taken literally, this rule
would make the documented Information Architecture impossible to build:
`ExperimentDetailPage`'s run table (per Architecture §7/§8) must render one
row per `run_id`, and each row self-fetches via the `runs` feature's
`useRunQuery` — a genuine, spec-mandated cross-feature dependency
(Integration Guide §7/§9's documented N+1 pattern).

## Options Considered

1. Forbid cross-feature imports entirely, and duplicate the run-fetching
   logic inside `features/experiments` instead.
2. Allow unrestricted deep imports between features
   (`features/runs/api/queries` from anywhere).
3. Allow cross-feature imports, but only through each feature's `index.ts`
   barrel — never by reaching into a feature's `api/`, `components/`,
   `hooks/`, or `utils/` subfolders directly.

## Decision

Option 3. A feature's `index.ts` is its public API. Other features (and
`app/`) may only import from `@/features/<name>`, never from
`@/features/<name>/<anything-deeper>`. `app/pages` is exempt from this rule
for the one case where a page needs a component that a feature has not
(yet) chosen to re-export from its barrel (e.g. `RunTable` from
`@/features/experiments/components/RunTable` while that feature's barrel
intentionally stays scoped to types + queries) — pages sit above every
feature in the composition, so this is vertical, not lateral, coupling.

## Rationale

- Preserves the spirit of Architecture §23 (features don't reach into each
  other's plumbing) while permitting the composition the IA actually
  requires.
- Keeps a feature free to refactor its internal folder structure
  (`api/`, `hooks/`, `utils/`) without breaking any other feature, since
  the only contract other features depend on is the barrel's exports.
- Matches Engineering Spec §5's "API Design Rules": components never call
  `fetch()` directly; the same discipline now extends to features never
  reaching past each other's public surface.

## Consequences

- Every feature's `index.ts` documents this rule inline (see
  `src/features/*/index.ts`).
- A feature that wants to expose something to other features must
  deliberately re-export it from its barrel — nothing is accidentally
  importable.
- No lint rule enforces this yet (the project is small enough that code
  review is sufficient). If the codebase grows, an ESLint import-boundary
  rule (e.g. `eslint-plugin-boundaries`) would be the natural next step —
  revisit only if a violation actually slips through in practice.
