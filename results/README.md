# Run inventory

All setup attempts and smoke trials are retained. Only a completed full run that passes `audit.py --require-full` may supply the website table.

- [20261110T103041Z](20261110T103041Z/): Setup attempt stopped before measurements: Tempest worker entry point did not match the front controller.
- [20261110T103217Z](20261110T103217Z/): Setup attempt stopped before measurements: Tempest session/cookie middleware required an encryption key for these stateless API routes.
- [20261110T103356Z](20261110T103356Z/): Setup preflight failed: Tempest worker needed request-scoped exception handling to return expected 404/422 responses.
- [20261110T103538Z](20261110T103538Z/): Setup preflight failed: corrected the Tempest container helper namespace in the worker exception handler.
- [20261110T103707Z](20261110T103707Z/): Successful short smoke run: one two-second trial per case/contender, zero errors. Not a reference measurement. The Tempest worker used explicit per-request garbage collection in this smoke; the final fixture uses PHP automatic GC.

- [20261110T104256Z](20261110T104256Z/): **Audited full reference run**, 140 trials and 140 warmups, zero errors. Supplies the website table.
