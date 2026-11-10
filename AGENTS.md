# Benchmark rules

- Keep this repository runnable from a fresh clone with Docker Compose, Python and Bash, without sibling repositories.
- Use published stable framework releases on PHP 8.5. Freeze source checksums, runtime image digests and Composer locks; refresh explicitly.
- Never modify framework vendor source, cache benchmark responses, drop failed contenders, remove outliers, or publish smoke results as full measurements.
- Retain every trial, errors, effective settings and machine metadata. Report limitations and competitor wins.
- Run long builds and benchmarks in a visible hc terminal. Do not start other agents unless asked.
