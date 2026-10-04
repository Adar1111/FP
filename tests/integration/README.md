# integration

Component boundaries, persistence, and error propagation.

Run ingestion tests from the repository root with
`python -m unittest discover -s tests/integration -p test_ingest_measurement.py -v`
or `python tests/integration/test_ingest_measurement.py -v`.
Direct execution resolves the project imports relative to the test file, so it
also works from another working directory. This test-runner change does not
change the ingestion algorithm.

Ingestion tests isolate raw copies, SQLite metadata, and JSON event logs in a
temporary directory. Each test uses a separate logger and closes its handlers
before cleanup, including on Windows. Assertions cover success, duplicates,
and copy or insertion failure events. This changes test coverage only; the
ingestion algorithm version is unchanged.
