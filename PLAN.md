# PLAN.md — AHP Macro Valuation Dashboard

A statically-generated dashboard reproducing the macroeconomic free-cash-flow yield and related series from Atkeson, Heathcote & Perri (NBER WP 34748, 2026), with a fully automated weekly data refresh.

## 1. Goal

Build a small, robust, reproducible system with two cleanly separated halves:

- A **Python ETL pipeline** that downloads BEA NIPA and Federal Reserve Z.1 data, faithfully reconstructs the AHP series (including the FDI and closely-held equity imputations on enterprise value), and emits a versioned JSON artifact validated against a shared schema.
- A **SvelteKit static site** that consumes that artifact at build time and renders an interactive dashboard with brushable/zoomable LayerCake charts.

The two halves communicate exclusively through a JSON file conforming to a JSON Schema checked into the repo. Neither half may import from the other.

## 2. Architecture

```
                    weekly cron
                         │
                         ▼
   ┌─────────────────────────────────┐
   │  GitHub Actions: etl.yml        │
   │  ─ run pipeline                 │
   │  ─ check vintage vs manifest    │
   │  ─ if new: commit data/v1/*.json│
   └─────────────────────────────────┘
                         │ commit on main
                         ▼
   ┌─────────────────────────────────┐
   │  GitHub Actions: pages.yml      │
   │  ─ yarn build (SvelteKit)       │
   │  ─ deploy to GitHub Pages       │
   └─────────────────────────────────┘
```

The ETL never runs in the browser. The frontend never makes network requests at runtime. Everything the dashboard shows comes from `data/v1/dataset.json`, which is bundled into the static build.

## 3. Repository layout

```
/
├── pipeline/                       # Python ETL (uv-managed)
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── src/ahp_pipeline/
│   │   ├── __init__.py
│   │   ├── cli.py                  # `ahp-pipeline run`, `... check-vintage`
│   │   ├── config.py               # paths, URLs, env vars
│   │   ├── sources/
│   │   │   ├── bea.py              # BEA API client (NIPA Table 1.14)
│   │   │   └── fed_z1.py           # Z.1 bulk CSV downloader & parser
│   │   ├── transform/
│   │   │   ├── flows.py            # FCF, earnings from NIPA flows
│   │   │   ├── enterprise_value.py # EV with FDI + closely-held imputations
│   │   │   ├── capital.py          # K, net investment, growth rates
│   │   │   └── yields.py           # all derived ratios
│   │   ├── models.py               # pydantic models matching the schema
│   │   ├── validate.py             # accounting identity checks
│   │   ├── manifest.py             # vintage tracking
│   │   └── output.py               # JSON serialization
│   └── tests/
│       ├── conftest.py
│       ├── fixtures/               # tiny synthetic NIPA/Z.1 slices
│       ├── test_sources.py
│       ├── test_transform.py
│       ├── test_identities.py      # accounting invariants
│       └── test_output.py          # round-trip schema validation
│
├── app/                            # SvelteKit static site (yarn-managed)
│   ├── package.json
│   ├── yarn.lock
│   ├── svelte.config.js            # adapter-static, base path
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── postcss.config.cjs
│   ├── playwright.config.ts
│   ├── vitest.config.ts
│   ├── src/
│   │   ├── app.html
│   │   ├── app.css                 # tailwind directives
│   │   ├── lib/
│   │   │   ├── data/
│   │   │   │   ├── dataset.ts      # typed import of /data/v1/dataset.json
│   │   │   │   └── format.ts       # number/period formatters
│   │   │   ├── types/
│   │   │   │   └── dataset.d.ts    # GENERATED from schema, do not edit
│   │   │   ├── charts/
│   │   │   │   ├── LineChart.svelte
│   │   │   │   ├── TwinAxisChart.svelte
│   │   │   │   ├── BrushableLineChart.svelte
│   │   │   │   ├── Tooltip.svelte
│   │   │   │   └── axis/
│   │   │   └── components/
│   │   │       ├── StatCard.svelte
│   │   │       ├── ChartCard.svelte
│   │   │       └── DataFootnote.svelte
│   │   └── routes/
│   │       ├── +layout.svelte
│   │       ├── +page.svelte        # the dashboard
│   │       └── +page.ts            # load dataset.json at build time
│   └── tests/
│       ├── unit/                   # vitest
│       └── e2e/                    # playwright
│
├── schema/                         # SHARED contract — both halves depend on it
│   └── v1/
│       └── dataset.schema.json
│
├── data/                           # generated; committed by ETL workflow
│   └── v1/
│       ├── dataset.json
│       └── manifest.json           # vintage tracking, last-update timestamps
│
├── scripts/
│   ├── generate-types.sh           # json-schema-to-typescript → app/src/lib/types/
│   └── verify-types-fresh.sh       # CI guard: types match schema
│
├── .github/
│   └── workflows/
│       ├── ci.yml                  # PR validation
│       ├── etl.yml                 # weekly cron
│       └── pages.yml               # build & deploy
│
├── PLAN.md
├── AGENTS.md
├── README.md
└── LICENSE.md                      # Blue Oak Model License 1.0.0
```

## 4. Data contract (the most important section)

Both halves of the system depend only on `schema/v1/dataset.schema.json`. Changing the schema is a breaking change and requires bumping `v1` → `v2` (see §10).

### 4.1 Artifact shape

`data/v1/dataset.json`:

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-04-13T12:34:56Z",
  "sources": {
    "bea_nipa_table_1_14": {
      "vintage": "2026-03-27",
      "url": "https://apps.bea.gov/..."
    },
    "fed_z1": {
      "vintage": "2026-03-13",
      "release_quarter": "2025Q4",
      "url": "https://www.federalreserve.gov/releases/z1/..."
    }
  },
  "frequency": "quarterly",
  "periods": ["1952Q1", "1952Q2", "...", "2025Q3"],
  "series": {
    "fcf_yield": {
      "label": "Free cash flow yield",
      "description": "Free cash flow divided by enterprise value.",
      "unit": "ratio",
      "values": [0.045, 0.040, "..."]
    },
    "earnings_yield": { "...": "..." }
  },
  "stats": {
    "fcf_yield": { "mean": 0.0364, "std": 0.0127, "min": 0.007, "max": 0.078 }
  }
}
```

Design choices:

- `periods` is a single top-level array. Every series in `series.*.values` must have the same length as `periods` and align element-wise. The pipeline enforces this; the schema enforces it via `minItems`/`maxItems` cross-references (or, if JSON Schema can't express it cleanly, the pipeline asserts it and a unit test on the frontend asserts it again at load time).
- All values are stored as raw ratios (e.g., `0.0364`), never percentages. Formatting is the frontend's job.
- Missing values are encoded as `null`, never `NaN` or sentinel numbers. The schema permits `null` only where genuinely possible (early periods of late-starting series).
- `stats` is precomputed on the Python side so the frontend never has to recompute means and standard deviations.

### 4.2 Series to ship in v1

| Key | Definition | Source |
|---|---|---|
| `gva` | Corporate gross value added | NIPA 1.14 |
| `labor_compensation` | Compensation of employees, corporate | NIPA 1.14 |
| `taxes_total` | IBT + business transfers + corporate income/wealth taxes | NIPA 1.14 |
| `gross_investment` | Gross fixed capital formation, corporate | Z.1 S.5 + S.6 |
| `cfc` | Consumption of fixed capital, corporate | NIPA 1.14 |
| `net_investment` | `gross_investment − cfc` | derived |
| `fcf` | `gva − labor_compensation − taxes_total − gross_investment` | derived |
| `earnings` | `fcf + net_investment` | derived |
| `enterprise_value` | NFC + FB market equity + liabilities − financial assets, with FDI and closely-held imputations | Z.1 B.1 + L.224 + FEDS notes |
| `capital_replacement_cost` | Current-cost fixed assets, corporate | Z.1 L.4 |
| `fcf_yield` | `fcf / enterprise_value` | derived |
| `earnings_yield` | `earnings / enterprise_value` | derived |
| `ev_gva` | `enterprise_value / gva` | derived |
| `k_gva` | `capital_replacement_cost / gva` | derived |
| `fcf_gva` | `fcf / gva` | derived |
| `labor_share` | `labor_compensation / gva` | derived |
| `net_inv_v` | `net_investment / enterprise_value` | derived |
| `net_inv_k` | `net_investment / capital_replacement_cost` | derived |
| `k_v` | `capital_replacement_cost / enterprise_value` (inverse Tobin's Q) | derived |
| `payout_ratio` | `fcf / earnings` | derived |

### 4.3 TypeScript types

`app/src/lib/types/dataset.d.ts` is **generated** from `schema/v1/dataset.schema.json` via `json-schema-to-typescript` (run by `scripts/generate-types.sh`). It is checked into the repo so the frontend builds without re-running codegen, but CI verifies it is up to date via `scripts/verify-types-fresh.sh`. Editing it by hand is forbidden (see AGENTS.md).

## 5. Pipeline (Python)

### 5.1 Tooling

- **uv** for dependency, venv, and lockfile management
- **ruff** for lint and format
- **ty** (Astral's type checker) in strict mode
- **pytest** for tests
- **pydantic** v2 for schema models and ETL boundary validation
- **httpx** for HTTP (sync; async unnecessary at this scale)
- **polars** for data wrangling

`pyproject.toml` declares Python ≥ 3.13. All pipeline code is fully type-annotated.

### 5.2 Tasks

**Configuration and scaffolding.** Initialize `pipeline/` with `uv init`. Configure ruff, ty, pytest. Set up `src/ahp_pipeline/config.py` with:
- BEA API base URL and table identifiers
- BEA API key read from `BEA_API_KEY` env var (fail loudly if missing)
- Z.1 bulk download URL (`https://www.federalreserve.gov/datadownload/...` or `releases/z1/current/z1.zip`)
- Output paths

**BEA NIPA source (`sources/bea.py`).** Fetch NIPA Table 1.14 quarterly observations for the corporate sector via the BEA REST API. Parse into a polars DataFrame keyed by `(period, line_code)`. Cache the raw JSON response to `pipeline/.cache/` keyed by request hash so repeated runs during development don't re-hit the API. Capture vintage metadata (release date, last-updated timestamp) for the manifest.

**Fed Z.1 source (`sources/fed_z1.py`).** Download the Z.1 bulk ZIP, extract the CSVs we need (B.1 NFC, B.1 FB, L.4, L.224, S.5, S.6, plus the supporting tables for FDI imputations). Parse with polars. Cache the downloaded ZIP. Capture release vintage from the Z.1 release calendar embedded in the bundle. Use the BEA's NIPA Table 7.16/7.17 documentation to confirm line code mappings; document any line code that the agent had to look up.

**Transformations (`transform/*.py`).**

- `flows.py`: compute FCF and earnings from NIPA flows. Aligns quarterly NIPA flows (annualized in the source) so units are consistent with Z.1 stocks (end-of-quarter levels).
- `enterprise_value.py`: assemble enterprise value following the paper's definition. NFC + FB sum of market equity + liabilities − financial assets, with the imputed value of closely-held equity from the Fed's FEDS Notes methodology, plus FDI inward equity, minus FDI outward equity. The FDI imputations are non-trivial; the implementation must include a docstring referencing the relevant FEDS Notes URLs and the line items used. **Mark this as the highest-risk module — it is where reproduction can silently go wrong.**
- `capital.py`: pull `capital_replacement_cost` from Z.1 L.4 and compute `net_inv_k` and `k_v`.
- `yields.py`: compute all the derived ratios listed in §4.2.

**Validation (`validate.py`).** Run accounting identity checks as hard assertions before any output is written:

- `gva ≈ labor_compensation + taxes_total + gross_investment + fcf` (with float tolerance)
- `earnings − fcf ≈ net_investment`
- `net_inv_v ≈ net_inv_k * k_v` (equation 1 of the paper)
- All series have the same length as `periods`
- No NaN values; missing data is `None`
- The historical mean of `fcf_yield` over the full sample is in [0.030, 0.040] (sanity range; the paper reports 0.0364)

If any identity fails beyond tolerance, the pipeline exits non-zero and the workflow reports failure. **No silent fallbacks.**

**Output (`output.py`).** Build a pydantic model instance, dump to JSON with stable key ordering and 2-space indentation (so diffs are reviewable), validate against the JSON Schema as a final belt-and-braces check, and write to `data/v1/dataset.json`.

**Manifest (`manifest.py`).** Write `data/v1/manifest.json` containing source vintages, run timestamp, schema version, and a hash of `dataset.json`. The `check-vintage` CLI subcommand fetches only the BEA and Fed release metadata (not the full data) and compares against the existing manifest, exiting 0 if no new vintage is available and 1 if the workflow should proceed to a full run.

**CLI (`cli.py`).** Subcommands:
- `ahp-pipeline run` — full ETL
- `ahp-pipeline check-vintage` — cheap vintage probe for the cron job
- `ahp-pipeline validate` — re-validate an existing `data/v1/dataset.json` against the schema (used in CI)

### 5.3 Tests

- Unit tests on each transform with small synthetic input fixtures.
- Identity tests that load the real `data/v1/dataset.json` (if present) and re-run the validation suite — these are the strongest correctness signal and run in CI.
- Source tests use recorded HTTP fixtures (`pytest-httpx` or similar) so they don't hit the network.
- Schema round-trip test: build a dataset, serialize, reload, validate. Must be byte-identical.

## 6. Frontend (SvelteKit)

### 6.1 Tooling

- **yarn** (Berry, modern resolver) for package management
- **SvelteKit** latest, `@sveltejs/adapter-static`
- **TypeScript strict mode**, no `any`
- **Tailwind CSS v4**
- **LayerCake** for charts, with d3-scale, d3-shape, d3-array, d3-brush as needed
- **Vitest** for unit tests
- **Playwright** for e2e
- **ESLint + Prettier** with the SvelteKit defaults plus the Tailwind plugin

### 6.2 Tasks

**Scaffolding.** `yarn create svelte@latest app`, choose the Skeleton project + TypeScript + ESLint + Prettier + Playwright + Vitest. Configure `adapter-static` with `fallback: 'index.html'`. Set the `paths.base` in `svelte.config.js` to read from `BASE_PATH` env var (empty by default, set to `/<repo-name>` for GitHub Pages). Install Tailwind v4 per its current Vite plugin setup. Strip the default boilerplate.

**Type generation.** Add `scripts/generate-types.sh` that runs `json-schema-to-typescript` on `schema/v1/dataset.schema.json` and writes `app/src/lib/types/dataset.d.ts`. The generated file has a header comment marking it auto-generated. Add a yarn script `types:generate` and a yarn script `types:check` that runs the verifier.

**Data loading.** `app/src/lib/data/dataset.ts` does a static `import dataset from '../../../../data/v1/dataset.json'` with the generated type. SvelteKit/Vite inlines this at build time. Add a runtime assertion (in dev only) that `Object.values(dataset.series).every(s => s.values.length === dataset.periods.length)`.

**Formatting helpers.** `app/src/lib/data/format.ts` exports `formatPercent`, `formatRatio`, `formatPeriod`, `parsePeriod` (returns a Date for the quarter midpoint, used for chart x-axes).

**Chart components.** Build LayerCake-based components in `app/src/lib/charts/`:

- `LineChart.svelte` — single or multi-series line chart with hover tooltip and configurable horizontal reference lines (used for the FCF-yield mean and −1σ).
- `TwinAxisChart.svelte` — two y-axes with independent scales (Figure 2: FCF/GVA vs 1 − labor share).
- `BrushableLineChart.svelte` — `LineChart` plus a small overview strip below with a d3-brush for date-range selection. The brush state is local component state; no URL sync in v1.
- `Tooltip.svelte` — shared tooltip primitive reading values from the LayerCake context.

All charts are responsive via LayerCake's built-in resize handling. No fixed widths.

**Page layout.** `app/src/routes/+page.svelte`:

1. Header: title, subtitle, last-update timestamp from `dataset.generated_at`, Z.1 vintage from `dataset.sources.fed_z1.vintage`.
2. Stat-card row: latest FCF yield, historical mean, deviation in pp, latest earnings yield, latest EV/GVA.
3. **Chart 1 (primary):** FCF yield with mean and −1σ reference lines. Brushable.
4. **Chart 2:** EV/GVA and capital/GVA on one axis (Figure 1). Brushable.
5. **Chart 3:** FCF/GVA vs (1 − labor share), twin-axis (Figure 2). Brushable.
6. **Chart 4 row:** two side-by-side panels — `net_inv_k` and `k_v` (Figure 5a, 5b). Brushable independently.
7. Footer: data sources, license, link to the AHP paper.

`+page.ts` exports `prerender = true`. There is no `+page.server.ts`. There is no client-side fetch.

### 6.3 Tests

- **Vitest:** unit tests on `format.ts`, on `lib/data/dataset.ts`'s alignment assertion, on any pure helpers.
- **Playwright:** e2e smoke tests against the built static site:
  - Page renders without console errors
  - All four charts mount and contain at least one `<path>`
  - Stat cards display non-empty values
  - Brushing on the primary chart updates the visible domain
  - Hovering a chart shows a tooltip

Playwright runs against `yarn build && yarn preview` in CI.

## 7. CI / CD

### 7.1 `ci.yml` — runs on PRs and pushes to non-main branches

Jobs (parallel where possible):

- **pipeline-lint-and-test:** uv sync, `ruff check`, `ruff format --check`, `ty check`, `pytest`.
- **app-lint-and-test:** yarn install --immutable, `yarn lint`, `yarn check` (svelte-check), `yarn test:unit`, `yarn test:e2e`, `yarn build`.
- **schema-types-fresh:** runs `scripts/generate-types.sh` into a temp dir and diffs against the committed `dataset.d.ts`. Fails if drift.
- **dataset-validate:** runs `ahp-pipeline validate` against the committed `data/v1/dataset.json`. Fails if it doesn't conform to the current schema or fails identity checks.

### 7.2 `etl.yml` — weekly cron, manually triggerable

Schedule: `0 6 * * 1` (Mondays 06:00 UTC). Steps:

1. Checkout main with write permissions.
2. Set up uv and Python.
3. `ahp-pipeline check-vintage`. If it exits 0 (no new vintage), stop here.
4. `ahp-pipeline run` to regenerate `data/v1/dataset.json` and `data/v1/manifest.json`.
5. `ahp-pipeline validate` as a hard gate.
6. If `git status` shows changes under `data/v1/`, commit them with a message like `data: refresh to Z.1 vintage 2026-06-12 / NIPA vintage 2026-05-30 [skip ci]` and push to main.
7. Trigger `pages.yml` via `workflow_dispatch`.

Secrets used: `BEA_API_KEY`. Permissions: `contents: write`, `actions: write`.

### 7.3 `pages.yml` — build and deploy to GitHub Pages

Triggers: push to main affecting `app/**`, `data/**`, `schema/**`, or manual dispatch from `etl.yml`. Standard GitHub Pages deployment using the official `actions/deploy-pages@v4` workflow. Sets `BASE_PATH=/<repo-name>` so the SvelteKit build emits the right asset paths.

## 8. Local development

Documented in README.md. Minimum:

```bash
# pipeline
cd pipeline
uv sync
export BEA_API_KEY=...
uv run ahp-pipeline run

# frontend
cd app
yarn install
yarn dev
```

A root-level `Makefile` or `justfile` with targets `pipeline-run`, `app-dev`, `app-build`, `test-all`, `lint-all` is acceptable but optional — the agent may add one if it improves DX.

## 9. Documentation

- **README.md:** project description; one-screen quick start; data sources block listing BEA NIPA, Fed Z.1, and the AHP paper, each with their licensing terms (BEA and Fed data are public-domain US Government works; cite the AHP paper for methodological credit); deployment notes; license.
- **PLAN.md** (this file): kept as a reference.
- **AGENTS.md:** rules for AI agents and humans modifying the repo.

## 10. Versioning the data contract

`schema/v1/` is frozen once published. Any non-additive change (renaming a field, removing a series, changing units) requires creating `schema/v2/` and `data/v2/`, regenerating types into a parallel `lib/types/v2/`, and updating the frontend to consume v2. Both versions may coexist temporarily. The frontend pins to one major version at a time. This is overkill today and indispensable on the first breaking change.

## 11. Out of scope for v1

- Nowcasting / EV roll-forward between Z.1 vintages
- S&P 500 cross-validation overlay
- Dark mode
- Recession shading
- CSV downloads
- Log-scale toggle
- Methodology drawer
- The earnings-yield overlay in the FCF-yield chart (not in the v1 chart list)

These are explicit non-goals — the agent must not add them speculatively.

## 12. Phasing

The agent should work in roughly this order, but **may interleave or reorder where it improves quality.** Commit boundaries are at the agent's discretion subject to the rules in AGENTS.md.

1. Repo scaffold, license, README skeleton, empty PLAN/AGENTS in place.
2. `schema/v1/dataset.schema.json` and the type-generation script — **before** either half is built, since both depend on it.
3. Python pipeline: scaffold, sources, transforms, validation, output, CLI, tests.
4. First successful end-to-end pipeline run committing a real `data/v1/dataset.json`.
5. SvelteKit app: scaffold, data loading, formatters, one chart end-to-end (the primary FCF yield chart) before building the rest.
6. Remaining charts and stat cards.
7. Frontend tests (vitest + Playwright).
8. CI workflows.
9. ETL cron workflow and Pages deployment workflow.
10. End-to-end verification on a real GitHub Pages deployment.

Each phase is "done" when its tests pass and `ruff`/`ty`/`yarn lint`/`yarn check` are all green.
