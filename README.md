# OFDR Measurement Processing

Process already-acquired main and auxiliary signals. Recover a sweep reference and resample the main signal; do not implement physical laser feedback.

## Status

Structure only. An optional OpenAI client already exists. Ingestion, correction, database persistence, logging, API endpoints, and cloud deployment are not implemented yet.

## Repository map

- src/: reusable Python components; see src/README.md.
- tests/: unit, integration, and scientific validation tests.
- configs/: versioned templates without secrets.
- schemas/: future external data contracts.
- scripts/: thin command-line entry points.
- notebooks/: exploratory analysis.
- data/raw/: immutable original files, excluded from Git.
- data/processed/: derived arrays, excluded from Git.
- data/samples/: small reviewed examples safe to share.
- results/: per-run manifests, logs, and diagnostics, excluded from Git.
- reports/: curated figures, presentations, and final reports.
- experiments/: human-written experiment plans and observations.
- docs/: architecture, setup, decisions, and open questions.

Start with [architecture](docs/architecture.md), [setup](docs/setup.md), and [open questions](docs/open-questions.md). Follow [AGENTS.md](AGENTS.md). No API key is required to inspect or develop the skeleton.
