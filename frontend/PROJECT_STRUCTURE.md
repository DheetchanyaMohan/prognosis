# Prognosis Frontend — Project Structure Reference

This document maps every directory and file in the project to the responsibility
assigned to it by the three source-of-truth documents: the **Product & UX
Architecture** doc, the **Backend Frontend Integration Guide**, and the
**Engineering Spec**. Status markers show what's real today:

- ✅ **Implemented** — working logic, calls the real backend, no fabrication.
- 🔲 **Scaffold only** — file exists, types/props are correct, body is a stub
  (`return null` or a thrown "not implemented") with a comment describing
  exactly what it will do. No business logic yet.
- ⬜ **Reserved, empty** — folder exists per the architecture, holds a
  `.gitkeep`, nothing has needed to live there yet.

---

## Root

```
prognosis-frontend/
├── .env.example              ✅  Documents VITE_API_BASE_URL, VITE_APP_NAME (Eng. Spec §22)
├── .gitignore                ✅  Vite default (node_modules, dist, editor files)
├── .oxlintrc.json             ✅  Linter config (oxlint, ships with the Vite template)
├── components.json            ✅  shadcn/ui config (style, aliases) — hand-authored;
│                                   see note below on why the CLI wasn't used
├── docs/
│   └── adr/                    ✅  Architecture Decision Log (Eng. Spec §21):
│                                    ADR-001 (native fetch), ADR-002 (barrel-only
│                                    cross-feature imports)
├── index.html                 ✅  Vite entry HTML
├── package.json                ✅  Dependencies, matches Eng. Spec §1 exactly
├── public/
│   └── favicon.svg             ✅  Static asset served as-is
├── tsconfig.json                ✅  Project references + `@/*` path alias
├── tsconfig.app.json              ✅  Strict mode, `@/*` alias, erasableSyntaxOnly
├── tsconfig.node.json              ✅  Vite config's own tsconfig (unmodified template)
└── vite.config.ts                  ✅  React + Tailwind v4 plugins, `@` → `src` alias
```

**Note on `components.json`:** the `shadcn` CLI fetches its component registry
from `ui.shadcn.com`, which isn't reachable from this environment's network
allow-list. The config and theme tokens below were hand-authored to match what
the CLI would have generated (`style: new-york`, neutral base color, CSS
variables). No actual Radix-based components (Dialog, Popover, etc.) have been
pulled in yet — only the plain-HTML primitives in `components/ui` exist so far,
since nothing built yet needs a Radix primitive.

---

## `src/` — top level

```
src/
├── main.tsx        ✅  Entry point: mounts <App /> inside <StrictMode>
├── index.css        ✅  Tailwind v4 import + shadcn CSS variable theme (light/dark)
├── vite-env.d.ts     —  Not present; not needed (no ambient Vite types referenced
│                        beyond what @vitejs/plugin-react already provides)
├── app/              →  see below
├── features/          →  see below
├── components/ui/      →  see below (shared UI primitives)
├── lib/                 →  see below (framework-agnostic infrastructure)
├── hooks/          ⬜  Reserved for cross-feature hooks. Empty today — Eng.
│                       Spec §7: no client state has been complex/shared enough
│                       across features to warrant one yet. Feature-local hooks
│                       live in `features/*/hooks` instead.
├── types/          ⬜  Reserved for types shared across ≥2 features. Empty
│                       today — every type so far belongs to exactly one
│                       feature and lives in that feature's own `types/`.
├── styles/         ⬜  Reserved for additional stylesheets if `index.css`
│                       ever needs to be split up. Empty today.
└── assets/          ⬜  Static imports (images, etc.) bundled by Vite. Only the
                          template's placeholder `vite.svg` remains.
```

---

## `src/app/` — application shell (routing, providers, layout, pages)

This is the one folder that's allowed to know about everything else — it
composes features together but contains no feature-specific business logic
itself (Eng. Spec §3, §8 "Page Components... never contain business logic").

```
app/
├── App.tsx                     ✅  Composition root: ErrorBoundary → AppProviders → RouterProvider
├── ErrorBoundary.tsx            ✅  Class-based React error boundary — the "App Error"
│                                     level from Eng. Spec §13. Catches unexpected render
│                                     exceptions only; never used for 404 or null
│                                     summary/diagnostics, which are expected states
│                                     handled explicitly by each page.
├── providers/
│   ├── AppProviders.tsx          ✅  Wraps the app in QueryClientProvider. The single
│   │                                  place new cross-cutting providers get added.
│   └── query-client.ts            ✅  The TanStack QueryClient instance + global
│                                       defaultOptions: retry policy (never retry 404/
│                                       validation errors, retry network/5xx twice),
│                                       refetchOnReconnect/refetchOnWindowFocus (Eng.
│                                       Spec §6). Per-query staleTime/refetchInterval
│                                       overrides live in each feature's queries.ts.
├── router/
│   └── router.tsx                  ✅  The route tree (createBrowserRouter), matching
│                                        Architecture §6 / Eng. Spec §4 exactly:
│                                        /                                       → redirect
│                                        /experiments                           → list ✅
│                                        /experiments/:experimentId             → detail 🔲
│                                        /experiments/:experimentId/runs/:runId → run 🔲
│                                        *                                      → 404 ✅
├── layouts/
│   ├── AppLayout.tsx                 ✅  <TopNav /> + <Outlet />. The single nested
│   │                                     layout every route renders inside.
│   └── TopNav.tsx                     ✅  Logo (→ /experiments), breadcrumb read from
│                                          route params, <HealthIndicator />. Matches
│                                          Architecture §5 exactly — no search, no
│                                          filters, no user menu (none are backed by
│                                          anything today).
└── pages/
    ├── ExperimentListPage.tsx           ✅  Fully wired: useExperimentsQuery, skeleton/
    │                                        empty/error states, renders ExperimentCard[].
    ├── ExperimentDetailPage.tsx           ✅  Fully wired: useExperimentQuery, skeleton/
    │                                          404/network/generic error states, header
    │                                          (name/description/created date), <RunTable>.
    ├── RunDetailPage.tsx                   ✅  Fully wired via useRunDetail: skeleton/
    │                                            404/network/generic error states, then
    │                                            RunHeaderBand → DiagnosisPanel →
    │                                            SummaryPanel → ConfigPanel in strict
    │                                            visual-hierarchy order (Architecture §10).
    └── NotFoundPage.tsx                     ✅  Catch-all 404 — renders <ErrorState variant="not-found">.
```

---

## `src/features/` — the three domain modules

Feature-first, not type-first (Eng. Spec Principle 3). `experiments` and
`runs` never import each other's internals — only `components/ui` and
`lib/api` (Architecture §23). Each feature follows the same internal shape:
`api/` (queries), `components/` (presentation), `hooks/` (feature-local
hooks), `types/` (response shapes), `utils/` (pure functions), `index.ts`
(public barrel — the *only* thing other code should import from).

### `features/health/` — liveness indicator only

```
health/
├── index.ts                  ✅  Re-exports types + queries
├── api/queries.ts              ✅  getHealth(), useHealthQuery() — staleTime 0,
│                                    refetched every 45s (Eng. Spec §6: "Health —
│                                    Always fresh").
├── components/
│   └── HealthIndicator.tsx      ✅  The nav-bar dot. Quiet by default; only
│                                     visually notable when status is "degraded".
│                                     `llm_provider: "not_configured"` never reads
│                                     as an error (Integration Guide §3, §8).
├── hooks/                    ⬜  Reserved — nothing feature-local needed yet.
├── types/index.ts               ✅  HealthResponse, ComponentHealth — exact
│                                     mirror of the Pydantic model.
└── utils/                     ⬜  Reserved — no derived logic needed yet.
```

### `features/experiments/` — list + detail

```
experiments/
├── index.ts                        ✅  Re-exports types + queries
├── api/queries.ts                    ✅  getExperiments(), getExperiment(id),
│                                          useExperimentsQuery() (staleTime 5 min),
│                                          useExperimentQuery(id) (staleTime 5 min).
├── components/
│   ├── ExperimentCard.tsx               ✅  One card per experiment; whole card is
│   │                                        a keyboard-operable Link. Monospace name,
│   │                                        "No description" placeholder, run count.
│   ├── ExperimentCardSkeleton.tsx         ✅  Matches ExperimentCard's exact dimensions
│   │                                          (Architecture §14: skeletons, not spinners).
│   ├── RunTable.tsx                        ✅  One RunRow per run_id; "No runs yet"
│   │                                            EmptyState when the list is empty.
│   └── RunRow.tsx                            ✅  Self-fetches via useRunQuery(runId) —
│                                                  the N+1 pattern (Integration Guide
│                                                  §7/§9), deliberately not batched.
│                                                  ID renders immediately; StatusBadge +
│                                                  best val loss shimmer in independently
│                                                  while that row's own request resolves.
│                                                  Imports useRunQuery/deriveRunStatus/
│                                                  StatusBadge from @/features/runs (the
│                                                  barrel) per ADR-002.
├── hooks/                            ⬜  Reserved — nothing feature-local needed yet.
├── types/index.ts                      ✅  ExperimentRecord — exact mirror of the model.
└── utils/                              ⬜  Reserved — no derived logic needed yet.
```

### `features/runs/` — the diagnosis report (richest feature)

```
runs/
├── index.ts                          ✅  Barrel — types + queries + hooks/useRunDetail +
│                                          utils/deriveRunStatus + components/StatusBadge
│                                          (added this slice — RunRow needed it).
│                                          Documents the barrel-only cross-feature
│                                          import rule (ADR-002) inline.
├── api/queries.ts                      ✅  getRun(id), useRunQuery(id) — staleTime 0,
│                                            refetchInterval enabled ONLY while
│                                            summary/diagnostics are null, disabled
│                                            the instant both populate (Eng. Spec §6).
├── components/
│   ├── RunHeaderBand.tsx                  ✅  Run ID as h1 + StatusBadge.
│   ├── StatusBadge.tsx                     ✅  Presentational — icon + tone + label
│   │                                           per flag, supports multi-flag display.
│   ├── DiagnosisPanel.tsx                    ✅  Three cards + BestEpochCard, or a
│   │                                              single "Analysis pending" PendingCard.
│   ├── GapCard.tsx                             ✅  Trend badge + capped loss_gap_pct +
│   │                                                  accuracy gap; caveats "stable" when
│   │                                                  total_epochs < 4.
│   ├── PlateauCard.tsx                          ✅  Three distinct states: plateaued /
│   │                                                  not plateaued / insufficient_data.
│   ├── InstabilityCard.tsx                       ✅  Empty spike_epochs renders as a
│   │                                                   reassuring "No instability found".
│   ├── BestEpochCard.tsx                           ✅  StatCard grid from diagnostics.best_epoch.
│   ├── SummaryPanel.tsx                             ✅  Lead sentence + 8-stat grid +
│   │                                                     "Diverged early" badge from
│   │                                                     summary.diverged.
│   └── ConfigPanel.tsx                               ✅  Dataset/Model/Training groups;
│                                                           gradient_clip_norm null → "disabled".
├── hooks/
│   └── useRunDetail.ts                  ✅  View-model hook for RunDetailPage: wraps
│                                            useRunQuery, folds in deriveRunStatus,
│                                            isDiverged (from summary.diverged),
│                                            isSummaryPending/isDiagnosticsPending.
│                                            Named for what it serves (the Run Detail
│                                            page), not narrowly for diagnosis, since
│                                            it may grow beyond that.
├── types/index.ts                        ✅  RunConfig, RunSummaryResponse,
│                                              RunDiagnostics (+ all nested sub-types:
│                                              GeneralizationGap, PlateauDiagnostic,
│                                              InstabilityDiagnostic, BestEpochDiagnostic),
│                                              RunDetailResponse — exact mirrors.
└── utils/
    ├── deriveRunStatus.ts                  ✅  Implements the exact Architecture §10
    │                                            rules: overfitting/stalled/unstable/
    │                                            healthy/pending, multi-flag capable.
    └── format-run-stats.ts                   ✅  formatWallClock() — runs-domain
                                                    formatting stays here, not in lib/
                                                    (per architectural review).
```

---

## `src/components/ui/` — shared, domain-agnostic primitives

Per Eng. Spec §8: "They should know nothing about experiments or runs."
`StatusBadge` therefore lives in `features/runs/components`, not here, even
though the architecture doc calls it "shared" — it's shared *within the runs
domain* (Run Detail + eventually the run table), not domain-agnostic.

```
components/ui/
├── index.ts            ✅  Barrel — the only import path components should use
├── Card.tsx              ✅  Base bordered surface (+ CardHeader/CardTitle/CardContent)
├── Badge.tsx               ✅  Pill with tone + icon + label — never color alone
│                                (Accessibility §17). Semantic tones (healthy/
│                                caution/concern/informational) are reserved
│                                exclusively for diagnosis states (Architecture §20).
├── Button.tsx                ✅  Plain <button> wrapper, 3 variants. Identified in
│                                   Eng. Spec §8's component list, added now that a
│                                   second real consumer (ExperimentListPage's retry
│                                   action) existed.
├── Skeleton.tsx                 ✅  Generic shimmer block; feature skeletons compose
│                                     it into their own final-layout dimensions.
├── PendingCard.tsx                ✅  Shared "not an error" nullable-data state —
│                                       reused for Analysis pending / Training in
│                                       progress / checking-again-shortly polling
│                                       (aria-live="polite").
├── ErrorState.tsx                   ✅  Three visually/textually distinct variants:
│                                         not-found / network / generic (Architecture §15).
└── StatCard.tsx                       ✅  Typographic single-value stat — no
                                            fabricated sparklines (Architecture §12).
```

**Not yet built, deliberately:** `Tooltip` was named in Eng. Spec §8's example
list, but nothing in the product currently needs one — adding it now would be
the "unnecessary abstraction" the Non-Goals section warns against. Add it the
first time a real screen needs it.

---

## `src/lib/` — framework-agnostic infrastructure

Nothing here imports from `features/` or `app/` — dependencies point one
direction only.

```
lib/
├── utils.ts               ✅  cn() — clsx + tailwind-merge, used by every
│                                styled component instead of string concatenation.
├── config.ts                 ✅  The one place import.meta.env is read (Eng. Spec
│                                  §22) — apiBaseUrl, appName.
├── format-date.ts              ✅  formatBackendDate() — treats the backend's
│                                    naive-UTC ISO strings correctly.
└── api/
    ├── client.ts                 ✅  Thin fetch wrapper: base URL, timeout (10s),
    │                                  JSON parsing, HTTP status → typed error
    │                                  mapping. No caching, no retries, no reshaping
    │                                  — those belong to React Query / selectors.
    ├── endpoints.ts                 ✅  URL builders for exactly the 4 documented
    │                                     routes (health, experiments, experiment,
    │                                     run). Nothing else — no compare/agent/
    │                                     metrics endpoints, since they don't exist.
    └── errors.ts                     ✅  ApiError / NotFoundError / NetworkError /
                                            ValidationError — lets React Query and
                                            the UI distinguish failure modes without
                                            an error `code` field the backend
                                            doesn't provide.
```

---

## Everything NOT in this project, on purpose

Per Architecture §6, §24, §25 and Integration Guide §9 — absent because the
backend doesn't support them yet, not because they were forgotten:

- No `/compare` route, no comparison components, no `compare_runs` API call.
- No `/agent` route, no chat/hypothesis UI, no LangGraph-invoking API call.
- No `/settings` route.
- No global store (Redux/Zustand/Context-for-server-data) — server state
  lives exclusively in TanStack Query.
- No raw metrics / learning-curve chart component, no Recharts usage yet
  (installed per the stack, unused until a metrics endpoint exists).
- No pagination, filtering, or search UI on either list screen.
- No auth — no login page, no protected routes, no user context.

---

## What's left

Every route now has a fully implemented page. Remaining documented gaps are
all Future Enhancements blocked on backend capability (Architecture §24/§25):
run comparison, agent interaction, learning-curve charts, search/pagination,
multi-user auth — none of which exist in the API yet.
