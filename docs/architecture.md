# Architecture

## Scope

Process already-acquired OFDR signals using an auxiliary-interferometer reference. No physical laser feedback. The scientific model, calibration, units, and acceptance thresholds remain open until confirmed with the supervisor and sample data.

## Pipeline

Ingest -> validate -> align -> recover ruler -> construct grid -> resample -> reconstruct -> evaluate -> persist/report.

The numerical core must be callable locally without a server, database, or model API. Reuse algorithms, analysis, preprocessing, simulation, and visualization; do not create duplicate packages with overlapping roles.

## Tracking

A measurement identifies the acquisition, channel files, hashes, units, timing, and settings. A run identifies one processing attempt with parameters, code revision, environment, events, and outputs. Original files are immutable. Every attempt creates a new run. Never silently substitute guessed scientific metadata or overwrite previous results.

Store large arrays in artifact storage; metadata and relationships belong in a database. A future shared system can use PostgreSQL. Never concurrently edit SQLite through a file-sync directory.

## Quality

Execution completion and scientific validity are separate. A completed job can have failed or unassessed quality. Undefined thresholds mean unassessed, never passed. A missing algorithm returns an explicit unavailable/not-implemented outcome rather than a fabricated successful correction.

## Shared system

Two users will submit data and view separate runs through an API. Shared infrastructure will include authentication, metadata persistence, durable file storage, and eventually a worker. Choose hosting and queue technology after measuring workload needs.

## AI

Optional AI reads sanitized diagnostics, explains errors, and suggests investigations. It must not block ordinary processing or determine scientific validity. Preserve AI suggestions separately from numerical outputs.

## Next milestone

Implement local file ingestion and tracking with clearly labeled fixtures. Scientific schemas remain provisional. Then add run tracking and an explicit unavailable-processor response, before adding the scientific method.
