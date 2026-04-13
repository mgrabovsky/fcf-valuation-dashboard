# AGENTS.md

Rules and conventions for AI coding agents (and humans) working in this repository. Read this file in full before making any change. PLAN.md describes *what* to build; this file describes *how* to build it and *what not to touch*.

## 1. Project in one paragraph

This repo produces a static dashboard reproducing the macroeconomic free-cash-flow yield series from Atkeson, Heathcote & Perri (NBER WP 34748, 2026). It has two cleanly separated halves: a Python ETL pipeline (`pipeline/`) that downloads BEA NIPA and Federal Reserve Z.1 data and emits a JSON artifact, and a SvelteKit static site (`app/`) that renders that artifact. The two halves communicate exclusively through `data/v1/dataset.json`, which conforms to `schema/v1/dataset.schema.json`. The system is deployed to GitHub Pages and refreshed weekly by a GitHub Actions cron job.

## 2. Architectural invariants (sacred)

Violating any of these is a bug, even if tests pass.

1. **The two halves never import from each other.** Python code never reads anything under `app/`. TypeScript code never reads anything under `pipeline/`. The only shared artifact is `schema/v1/` and `data/v1/`.
2. **The frontend makes no network requests at runtime.** All data is bundled at build time via a static JSON import. There is no `+page.server.ts`, no `fetch()` to an API, no client-side data loading. `prerender = true` everywhere.
3. **The pipeline never runs in CI for PRs that don't touch it.** Full ETL runs only in `etl.yml` (cron) or on manual dispatch. PR CI runs `ahp-pipeline validate` against the committed dataset, not a fresh download.
4. **The data contract is sacred.** `schema/v1/dataset.schema.json` may be extended additively (new optional fields, new series) without a version bump. Any non-additive change (rename, remove, type change, unit change) requires creating `schema/v2/` and migrating the frontend. Never edit `v1` in a breaking way.
5. **`app/src/lib/types/dataset.d.ts` is generated, not handwritten.** Editing it directly is forbidden. To change it, change the schema and run `scripts/generate-types.sh`.
6. **No silent fallbacks in the pipeline.** If a source is unreachable, a line code is missing, or an accounting identity is violated beyond tolerance, the pipeline exits non-zero. Never paper over a data problem with a default value, an `except: pass`, or a "best effort" merge.
7. **All values in the artifact are raw ratios, not percentages.** `0.0364`, never `3.64`. Formatting belongs to the frontend.
8. **No client-side recomputation of stats.** Means, standard deviations, min/max are computed in Python and stored under `dataset.stats`. The frontend reads them.
9. **Periods are aligned by index, not by lookup.** `dataset.periods[i]` corresponds to `dataset.series.<key>.values[i]` for every series. The pipeline asserts this; the frontend asserts it again at load time in dev mode.

## 3. Tooling

### Python (pipeline)

| Concern | Tool |
|---|---|
| Python version | 3.13+ |
| Dependency manager | `uv` |
| Lint + format | `ruff` |
| Type checker | `ty` (Astral), strict mode |
| Tests | `pytest` |
| Data validation | `pydantic` v2 |
| HTTP | `httpx` (sync) |
| DataFrames | `polars` |

Do not introduce pandas, requests, mypy, black, or isort. They overlap with the chosen tools and create inconsistency.

### TypeScript / Svelte (app)

| Concern | Tool |
|---|---|
| Package manager | `yarn` (Berry) |
| Framework | SvelteKit (latest), `@sveltejs/adapter-static` |
| Language | TypeScript, strict mode |
| Build | Vite (SvelteKit default) |
| Styling | Tailwind CSS v4 |
| Charts | LayerCake (+ d3-scale, d3-shape, d3-array, d3-brush) |
| Unit tests | Vitest |
| E2E tests | Playwright |
| Lint + format | ESLint + Prettier (with Svelte and Tailwind plugins) |

Do not introduce npm, pnpm, Chart.js, ECharts, Plotly, Highcharts, or any UI component library. The dashboard is small enough to handcraft.

## 4. Running things

From the repo root:

```bash
# Pipeline
cd pipeline
uv sync
export BEA_API_KEY=...           # required, get from apps.bea.gov/api/signup
uv run ahp-pipeline run          # full ETL → data/v1/dataset.json
uv run ahp-pipeline check-vintage # cheap probe; exit 0 = nothing new
uv run ahp-pipeline validate     # re-validate the committed dataset
uv run pytest
uv run ruff check
uv run ruff format
uv run ty check

# Frontend
cd app
yarn install --immutable
yarn dev                         # dev server on http://localhost:5173
yarn build                       # static build → app/build/
yarn preview                     # serve the built site
yarn test:unit                   # vitest
yarn test:e2e                    # playwright (builds first)
yarn lint
yarn check                       # svelte-check
yarn types:generate              # regenerate dataset.d.ts from schema
yarn types:check                 # CI guard: types are fresh
```

## 5. Code style — Python

- All modules, functions, methods, and class attributes are fully type-annotated. `ty check` must pass with no errors.
- Use modern syntax: `list[int]`, `dict[str, float]`, `X | None`, `match` where it improves clarity.
- Prefer dataclasses or pydantic models over loose dicts at module boundaries. Inside a function, dicts and tuples are fine.
- Use `pathlib.Path` exclusively for paths. Never `os.path`.
- Polars idioms: prefer expressions (`pl.col(...)`) over column-by-column Python loops. Filter, group, and join at the DataFrame level.
- Avoid unnecessary OOP. A module of free functions is usually preferable to a class with one method. Use classes when state genuinely belongs together (e.g., a `BeaClient` holding the API key and a session).
- Docstrings on public functions and modules. Skip them on small private helpers and on tests. Use Google or NumPy style consistently.
- Comments explain *why*, not *what*. Code that needs a comment to explain *what* it does should usually be rewritten.
- Tests use plain `assert` and pytest fixtures. No `unittest.TestCase`.
- The `transform/enterprise_value.py` module is the highest-risk file in the pipeline and must include inline references (URLs to FEDS Notes and BEA documentation) for every line code and imputation it uses.

## 6. Code style — TypeScript / Svelte

- TypeScript strict mode. No `any`. No `as` casts except to narrow `unknown` from external boundaries.
- Use the generated types from `lib/types/dataset.d.ts`. Never re-declare dataset shapes inline.
- Svelte 5 runes (`$state`, `$derived`, `$effect`) where applicable. Don't mix runes with the legacy reactive `$:` syntax in the same component.
- Components have a single responsibility. A chart component renders a chart; it does not also fetch data, transform data, or own page layout.
- Tailwind classes go directly on elements. No `@apply` in component `<style>` blocks except for genuinely repeated patterns.
- No global CSS beyond `app.css` (Tailwind directives + a handful of base styles).
- Prefer `<script lang="ts">` everywhere. No `.js` files in `src/`.
- Format with Prettier; lint with ESLint. Both must pass.
- Keep `+page.svelte` thin: it composes components and passes data. Logic lives in `lib/`.

## 7. Commit rules

You decide commit boundaries. Follow these rules:

1. **Conventional Commits format:** `type(scope): subject`. Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`, `data`. Scopes: `pipeline`, `app`, `schema`, `ci`, `repo`. Examples:
   - `feat(pipeline): add Z.1 bulk downloader`
   - `feat(app): primary FCF yield chart`
   - `data: refresh to Z.1 vintage 2026-06-12`
   - `chore(repo): initial scaffold`
2. **One logical change per commit.** A commit that adds a feature, fixes an unrelated bug, and reformats three files is three commits.
3. **Never commit a broken build.** Before committing: lint, type-check, and run tests on the half you changed. If you changed both halves, run both. If you changed the schema, regenerate types and run both.
4. **Never commit secrets.** `BEA_API_KEY` lives in `.env.local` (gitignored) and in GitHub repository secrets. There is no `.env` file in the repo.
5. **Never commit generated files except the data artifact and the generated TypeScript types.** Both are committed deliberately so deployments are reproducible without re-running the pipeline.
6. **Commit messages explain why for non-obvious changes.** A one-line subject is fine for trivial changes; multi-line bodies are required when the change involves a tradeoff, a workaround, or a deviation from PLAN.md.
7. **Never use `git push --force` on `main`.** Force-push only to feature branches you own.
8. **Squash-merge fix-up commits before opening a PR.** The history on `main` should be readable.

## 8. Data contract rules

1. To add a series: extend the schema additively, regenerate types, implement the computation in the pipeline, add a unit test, add the series to `data/v1/dataset.json` via a normal pipeline run, and (optionally) wire it into the frontend. The pipeline must succeed on the new schema before the frontend uses the new series.
2. To add a stat: extend `dataset.stats` in the schema, compute it in `output.py`, regenerate types, use it in the frontend.
3. To add a source: add a module under `pipeline/src/ahp_pipeline/sources/`, register its vintage in the manifest, document its license in README.md.
4. Accounting identities live in `pipeline/src/ahp_pipeline/validate.py` and are checked on every run. When you add a derived series, add the corresponding identity check if one exists.
5. Float tolerance for identity checks: `1e-6` on ratios, `1e-3` on absolute dollar amounts. Document the choice in `validate.py`.

## 9. "Care zones" — touch these only when you mean it

| Path | Why |
|---|---|
| `schema/v1/` | Breaking changes require a v2 migration. Additive changes are fine but must be paired with a type regeneration. |
| `pipeline/src/ahp_pipeline/transform/enterprise_value.py` | Highest-risk module. The FDI and closely-held imputations are subtle and the paper is the authority. Changes here require an extra pair of eyes and a comment explaining what changed and why. |
| `pipeline/src/ahp_pipeline/validate.py` | Loosening a tolerance or removing an identity check is almost always the wrong fix. If an identity fails, the data or the transform is wrong. |
| `data/v1/dataset.json` | Generated. Never edit by hand. To change, edit the pipeline and rerun. |
| `app/src/lib/types/dataset.d.ts` | Generated. Never edit by hand. |
| `.github/workflows/etl.yml` | Wrong changes can cause the cron to silently stop refreshing data. Test in a feature branch with `workflow_dispatch` before merging. |

## 10. How to extend

### Add a new chart

1. Identify the series it needs. If they exist in the schema, skip to step 4.
2. Add the series to the schema (additively), regenerate types.
3. Implement the computation in the appropriate `pipeline/src/ahp_pipeline/transform/*.py` module, add a unit test, run the pipeline, commit the regenerated `dataset.json`.
4. Build the chart component in `app/src/lib/charts/` if a new chart type is needed; otherwise reuse `LineChart`/`TwinAxisChart`/`BrushableLineChart`.
5. Add the chart to `+page.svelte` in the right position.
6. Add a Playwright assertion that the chart mounts.

### Add a new data source

1. Module under `pipeline/src/ahp_pipeline/sources/`, exposing a function that returns a polars DataFrame and a vintage record.
2. Wire it into the relevant transform.
3. Add tests using recorded fixtures (no live network in tests).
4. Add the source to `dataset.sources` in the manifest and the schema.
5. Document the source and its license in README.md.

### Bump the schema to v2

1. Create `schema/v2/dataset.schema.json` with the new shape.
2. Generate `app/src/lib/types/v2/dataset.d.ts` via an updated script.
3. Update the pipeline to write `data/v2/dataset.json` *in addition to* v1 (parallel emission for one release cycle).
4. Update the frontend to consume v2.
5. Once stable, drop v1 in a follow-up commit. Update PLAN.md.

## 11. Testing requirements

- **Pipeline:** every transform module has a unit test. Every accounting identity has a dedicated test. The schema round-trip test must pass. New features add tests in the same commit.
- **Frontend:** every chart component has at least a "mounts and renders one path" Playwright test. Pure helpers (`format.ts`, etc.) have Vitest unit tests.
- **CI:** PR CI runs all of the above plus `ahp-pipeline validate` against the committed dataset. ETL CI additionally runs the full pipeline.
- A test that fails because the underlying data changed (e.g., a new vintage shifts a hardcoded value) is a fragile test and should be rewritten to assert a property, not a value.

## 12. CI expectations

- PR CI must pass before merge. No exceptions for "small" changes.
- Lint, type-check, and test must all be green.
- The `schema-types-fresh` check enforces that anyone modifying the schema also regenerated the TypeScript types. If it fails, run `yarn types:generate` and commit.
- The `dataset-validate` check enforces that the committed `data/v1/dataset.json` conforms to the current schema. If it fails after a schema change, run the pipeline locally and commit the refreshed dataset.

## 13. License and attribution

- Code is licensed under the Blue Oak Model License 1.0.0 (`LICENSE.md`).
- README.md must list all data sources and their licensing:
  - **BEA NIPA Table 1.14**: U.S. Government work, public domain (17 U.S.C. § 105).
  - **Federal Reserve Z.1 / Financial Accounts of the United States**: U.S. Government work, public domain.
  - **Atkeson, Heathcote & Perri (NBER WP 34748, 2026)**: cited for methodology; the working paper itself is © the authors, but the *methodology* is freely usable. Cite with full bibliographic detail.
- Do not vendor third-party code without checking the license. Do not copy code from Stack Overflow without attribution and license check.

## 14. Anti-patterns the agent should refuse

These come up specifically in projects like this. Refuse them even if asked.

- "Just hardcode the data for now." No. The pipeline exists for a reason; if it's broken, fix the pipeline.
- "Add a fallback so the build doesn't fail when BEA is down." No. The cached previous run is the fallback. The current run either succeeds or doesn't update the data.
- "Recompute the mean on the frontend so we don't have to regenerate the dataset." No. Stats live in the dataset.
- "Use `any` here, the type is complicated." No. The type is generated from the schema. If it's wrong, fix the schema.
- "Skip the identity check, it's off by 0.0001." No. Investigate why. The accounting identities are exact; floating-point error at that scale is suspicious.
- "Inline the chart logic in `+page.svelte`, it's only used once." No. Chart components live in `lib/charts/`. Page files compose, they don't implement.
- "Add a small client-side fetch to grab the latest data." No. The site is static. Refreshing data means rerunning the pipeline.
- "Bump the schema in place to add a field — it's only an addition." Additive changes are allowed, but you must still regenerate types and rerun the pipeline in the same commit, or CI will fail.

## 15. When in doubt

Re-read PLAN.md §4 (the data contract) and §2 (the architecture diagram). If a proposed change would violate either, it's the wrong change. If PLAN.md and AGENTS.md disagree, AGENTS.md wins for *how* and PLAN.md wins for *what*. If both are silent, prefer the smaller, more boring option and leave a note in the commit message.
