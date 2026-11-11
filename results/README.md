# Run inventory

All setup attempts and smoke trials are retained. Whole-table replacements require `audit.py --require-full`. Separately dated two-library additions require `audit.py --require-libraries` plus an audited full framework baseline; smoke results are never published.

- [20261110T103041Z](20261110T103041Z/): Setup attempt stopped before measurements: Tempest worker entry point did not match the front controller.
- [20261110T103217Z](20261110T103217Z/): Setup attempt stopped before measurements: Tempest session/cookie middleware required an encryption key for these stateless API routes.
- [20261110T103356Z](20261110T103356Z/): Setup preflight failed: Tempest worker needed request-scoped exception handling to return expected 404/422 responses.
- [20261110T103538Z](20261110T103538Z/): Setup preflight failed: corrected the Tempest container helper namespace in the worker exception handler.
- [20261110T103707Z](20261110T103707Z/): Successful short smoke run: one two-second trial per case/contender, zero errors. Not a reference measurement. The Tempest worker used explicit per-request garbage collection in this smoke; the final fixture uses PHP automatic GC.

- [20261110T104256Z](20261110T104256Z/): **Audited full reference run**, 140 trials and 140 warmups, zero errors. Supplies the seven existing framework rows, which remain unchanged when adding the separate ReactPHP/AMP measurements.
- [20261111T052854Z](20261111T052854Z/): ReactPHP/AMP setup attempt stopped at ReactPHP readiness: the `SO_REUSEPORT` setting needed to be nested under React Socket's TCP context. No measured results.
- [20261111T053202Z](20261111T053202Z/): ReactPHP/AMP smoke run exposed ReactPHP's pretty-printed JSON response, which failed the exact-byte Hello workload checker. Invalid for publication; all errors retained. The adapter now produces compact JSON and preflight checks exact Hello bytes.
- [20261111T053812Z](20261111T053812Z/): Successful ReactPHP/AMP smoke run: eight measured trials and eight warmups across all four cases, zero errors. Not a reference measurement. After this smoke, parent signal handlers were corrected to interrupt `wait()` for graceful shutdown; standalone container and regression tests verify the correction.
- [20261111T054427Z](20261111T054427Z/): Nine-contender run interrupted at the user's request to benchmark only the two added libraries. Partial results and cleanup logs retained; not used for website publication.
- [20261111T055316Z](20261111T055316Z/README.md): **Audited ReactPHP/AMP supplement**, twenty measured trials and twenty warmups for Hello and MySQL at 64 connections, zero errors. Adds only the two library rows, preserving the separately dated seven-framework baseline.
