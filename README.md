# FCF Valuation Dashboard

Static dashboard and reproducible ETL pipeline for the macroeconomic free-cash-flow valuation series in Atkeson, Heathcote, and Perri (NBER Working Paper 34748, 2026).

## Quick Start

```bash
# Pipeline
cd pipeline
uv sync
export BEA_API_KEY=...
uv run ahp-pipeline run

# Frontend
cd ../app
yarn install --immutable
yarn dev
```

## Repository Structure

- `pipeline/`: Python ETL using `uv`, `polars`, `pydantic`, `ruff`, `ty`, and `pytest`
- `app/`: SvelteKit static site using TypeScript, Tailwind CSS v4, LayerCake, Vitest, and Playwright
- `schema/v1/`: shared JSON Schema data contract
- `data/v1/`: committed artifact and manifest consumed by the frontend

## Data Sources

- **BEA NIPA Table 1.14**: U.S. Government work, public domain under 17 U.S.C. § 105.
- **Federal Reserve Z.1 / Financial Accounts of the United States**: U.S. Government work, public domain.
- **Atkeson, Andrew, Jonathan Heathcote, and Fabrizio Perri. 2026. "The Macroeconomic Free Cash Flow Yield." NBER Working Paper 34748.** Used for methodology attribution.

## Local Development

The frontend is fully static. It imports [`data/v1/dataset.json`](/home/mgrabovsky/code/10-web-experiments/fcf-valuation-dashboard/data/v1/dataset.json) at build time and makes no runtime network requests.

The pipeline fails loudly on missing inputs, source errors, or accounting-identity violations. There are no fallback values and no best-effort merges.

## Deployment

- `ci.yml`: lint, type-check, unit test, e2e test, schema freshness, dataset validation
- `etl.yml`: Monday cron to probe vintages and refresh `data/v1/`
- `pages.yml`: static build and deploy to GitHub Pages

## License

Blue Oak Model License 1.0.0. See [`LICENSE.md`](/home/mgrabovsky/code/10-web-experiments/fcf-valuation-dashboard/LICENSE.md).

