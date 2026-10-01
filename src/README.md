# Source boundaries

Retain the existing src package layout during scaffolding. Run future scripts from the repository root and import reusable components from src.

| Package | Responsibility |
| --- | --- |
| acquisition | Future instrument export adapters; no laser feedback |
| io | Read files without scientific correction |
| validation | Input checks and scientific quality criteria |
| preprocessing | Channel alignment and preparation |
| algorithms | Auxiliary-ruler recovery and resampling |
| analysis | Reconstruction and numerical metrics |
| simulation | Synthetic signals with known truth |
| processing | Coordinate stages and outcomes |
| visualization | Diagnostic plots |
| reporting | Assemble reports |
| storage | Metadata and artifact persistence |
| observability | Structured events and run correlation |
| api | Future shared-service adapters |
| ai | Optional log explanations and development assistance |

Numerical components must not depend on API, storage, or AI services. Processing coordinates numerical stages and persistence. API and scripts call processing. AI consumes selected diagnostics without changing scientific outcomes.

Package docstrings describe responsibilities; no processing behavior is implemented yet.
