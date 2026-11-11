# ReactPHP and AMP supplement — 11 November 2026

**Audited, complete for the two published library rows, zero errors.** This run adds ReactPHP HTTP and AMP HTTP Server to the website without rerunning or changing the [seven-framework baseline from 10 November](../20261110T104256Z/README.md).

This is a **separately dated supplement**, not a complete nine-contender run. Its `full_method` flag remains false. Do not treat the combined website table as one simultaneous head-to-head comparison.

## Method

- Intel Core i5-9400F, six logical CPUs, Fedora Linux 44, x86_64; rootless Docker 29.6.0, shared host with other containers running.
- Same recorded host/CPU model, pinned runtime images and PHP **8.5.12** as the baseline. CPU cores are not reserved.
- Two application workers per library; **2 CPU quota units / 2 GiB RAM** per app. Only one contender runs during each measurement. MySQL has 2 CPUs / 2 GiB; wrk has 4 CPUs / 512 MiB.
- Production OPcache, authoritative Composer classmaps, JIT off. Both event loops use **ext-event 3.2.0**.
- `GET /hello`: routed compact JSON; `GET /users/{id}`: one indexed MySQL read from the common 10,000-row fixture. Both use **64 persistent client connections** and the same response-checking wrk workload as the baseline.
- Five rotating rounds, **5 seconds warmup + 15 seconds measurement** each; no outlier removal. All trial ranges and errors retained.
- **20 measured trials, 20 warmups, four functional preflights**. Preflights also verify validation boundaries, even though validation throughput is outside this supplement's scope.
- **5,406,432 measured responses**, plus **1,830,662 warmup responses**; zero errors throughout.
- Started 2026-11-11T05:53:30.913438+00:00; completed 2026-11-11T06:01:34.739024+00:00.

## Results

Requests/s, median of five trials; ranges in brackets.

| HTTP library | Version | Hello / 64 | MySQL / 64 |
| --- | --- | ---: | ---: |
| ReactPHP HTTP | 1.12.0 | 40,998 [40,461–41,600] | 12,543 [12,481–12,757] |
| AMP HTTP Server | 3.4.8 | 14,001 [13,887–14,072] | 4,166 [4,124–4,192] |

ReactPHP has higher throughput in both measured cases. AMP has the lower median database p99 latency in this run (20.752 ms versus ReactPHP's 24.642 ms). See [summary.md](summary.md) for all latency and peak-memory results. These small synthetic endpoints do not predict full application capacity.

## Adapter details and limitations

These are HTTP libraries, **not full application frameworks**. Both fixtures add a router and explicit PHP input checks, with two supervised forked workers using `SO_REUSEPORT`. No vendor source is patched and no response cache is used.

- ReactPHP uses FastRoute and **react/mysql 0.6.0**, with round-robin distribution across ten lazy, queued native async connections per worker.
- AMP uses AMP Router and **amphp/mysql 3.1.2**, with its native connection pool capped at ten per worker.
- Both use a 600-second database idle timeout and native async drivers rather than blocking PDO in the event loop.
- This supplement's disposable MySQL account uses `mysql_native_password`, enabled on MySQL 8.4 because react/mysql 0.6 does not support the default authentication method. This differs from the historical baseline's account authentication. Runtime images, database fixture, workload and resource limits are otherwise pinned by the harness; the original baseline is not modified. This compatibility setting is not production deployment advice.
- Separate dates, shared-host scheduling and different database adapters limit cross-run comparisons. Closed-loop wrk latency is subject to coordinated omission. No TLS, authentication or application business logic is measured.

The exact harness is retained in [harness/](harness/), with application build-context hashes in [source-manifest.json](source-manifest.json). [versions.json](versions.json) records package references, extensions, event-loop classes and worker processes.

## Audit and reproduce

From the repository root:

```sh
python3 audit.py results/20261111T055316Z --require-libraries
BENCH_SERVICES=reactphp,amphp BENCH_CASES=hello,db BENCH_CONNECTIONS=64 ./run.sh
```

The supplemental audit requires exactly these two contenders and two cases, all five trials and warmups, complete preflights and zero errors. It cannot pass `--require-full`.

Update only the two website rows, preserving and independently auditing the existing framework baseline:

```sh
python3 add-libraries.py results/20261111T055316Z --baseline results/20261110T104256Z --site ../crabphp-site
```

Evidence: [audit.json](audit.json), [summary.json](summary.json), [trials.json](trials.json), [warmups.json](warmups.json), [preflight.json](preflight.json), [metadata.json](metadata.json), [compose-resolved.yaml](compose-resolved.yaml), individual wrk/resource/server logs and [cleanup.log](cleanup.log).
