# OFDR Project Instructions

## Project purpose

This project processes already-acquired OFDR measurements. The auxiliary-interferometer signal is the reference ruler used to recover the laser sweep coordinate and resample the main measurement signal onto an equal-frequency grid. The goal is a reproducible, validated correction and analysis pipeline.

The project does not control or physically tune the laser. Do not invent hardware feedback, real-time control, or closed-loop behavior unless the supervisor explicitly requests it.

## Role of AI

AI is a development assistant, not the scientific authority and not part of the numerical correction by default. It may help write code, inspect logs, summarize failures, suggest tests, and explain results. Every AI-generated algorithm or change must be reviewed, tested on known data, and traceable to a code version. Never present an AI suggestion as a validated scientific result.

## Architecture

- Keep numerical processing independent from the web/API layer and user interface.
- Organize processing into clear stages: input validation, channel alignment, auxiliary-signal analysis, frequency-grid construction, resampling, reconstruction, metrics, and reporting.
- Preserve the raw measurement files unchanged. Store processed outputs separately.
- Store metadata for every measurement and processing run: unique IDs, timestamps, acquisition settings, units, algorithm version, parameters, warnings, and software environment.
- A later shared service may expose the pipeline through an API, database, and file storage. The same processing functions must run locally and on the service.

## Scientific correctness

- Use explicit units and document coordinate conventions, sampling rates, channel ordering, delays, windows, interpolation methods, and sign conventions.
- Treat synchronization, noise/SNR, Nyquist limits, missing samples, clipping, and invalid auxiliary signals as first-class validation cases.
- Compare corrected and uncorrected results using defined metrics such as peak position, peak width, resolution, error, and attenuation-related quantities.
- Keep intermediate arrays and diagnostic plots available for debugging and audit.
- Do not silently discard samples, repair malformed data, or replace failed calculations with plausible-looking values. Fail clearly and record the reason.

## Reproducibility and data tracking

- Every run must have a run ID and a reproducible record of inputs, parameters, code version, and outputs.
- Never overwrite a previous run. Create a new run for changed parameters or code.
- Logs must include run ID, measurement ID, processing stage, severity, elapsed time, and actionable error details.
- Use deterministic processing where practical; record random seeds when randomness is used.
- Keep large raw data and generated results out of Git. Git stores code, schemas, configuration templates, documentation, and small test fixtures. Secrets and `.env` files must never be committed.

## Testing requirements

- Add unit tests for each numerical stage and integration tests for the complete pipeline.
- Maintain synthetic signals with known nonlinear sweeps and known expected results.
- Test the identity case: an already uniform frequency sweep should remain unchanged within tolerance.
- Test invalid input, channel-length mismatch, timing offset, noise, clipping, and insufficient auxiliary-signal quality.
- A change is complete only after relevant tests pass and diagnostic results have been inspected.

## Coding conventions

- All source code, comments, docstrings, logs, and filenames must be in English.
- Prefer small, typed, testable functions with explicit inputs and outputs.
- Do not place secrets, machine-specific paths, or unexplained constants in source code.
- Use clear exceptions and structured logging. Avoid broad silent `except` blocks.
- Document assumptions before implementing formulas or DSP methods. If the supervisor's specification is ambiguous, mark the assumption in the code and documentation.

## Safe workflow

1. Inspect existing code, schemas, sample data, and logs before changing behavior.
2. State the scientific assumption and expected output.
3. Implement the smallest testable change.
4. Run tests and inspect plots/diagnostics.
5. Record the algorithm version and update documentation.

Do not connect the system to physical laser control or make irreversible data changes without explicit supervisor approval.
