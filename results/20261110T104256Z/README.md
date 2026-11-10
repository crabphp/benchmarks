# Reference run — 10 November 2026

**Audited, complete, zero errors.** This run supplies the CrabPHP website table.

## Environment and method

- Intel Core i5-9400F, six logical CPUs, Fedora Linux 44, x86_64; 15.5 GiB visible to Docker.
- Rootless Docker 29.6.0; this is a shared machine with other containers running. CPU cores are not reserved.
- PHP **8.5.12** for every contender, JIT off, production OPcache, two application workers, 2-CPU quota and 2 GiB per app.
- Started 2026-11-10T10:43:22.360644+00:00; completed 2026-11-10T11:38:25.256858+00:00.
- Four cases × seven frameworks × five trials = **140 measured trials**, plus **140 warmups** and **28 functional preflights**.
- **44,794,924 measured responses**, plus 15,196,026 warmup responses. Every trial and warmup reported zero errors.
- Five-second warmup before every 15-second measurement. Contender order rotates each round.

Source harness: [`a5daf13`](https://github.com/crabphp/benchmarks/tree/a5daf13a76f3b615aeaf91f39b4274420d0abf67). The exact scripts are also retained in [`harness/`](harness/).

## Throughput

Requests/s, median of five trials. Full ranges, latency percentiles and memory are in [summary.md](summary.md).

| Framework | Version | Hello / 64 | Hello / 256 | MySQL / 64 | Validation / 64 |
| --- | --- | ---: | ---: | ---: | ---: |
| Crab | 0.6.4 | 108,522 | 109,632 | 20,240 | 56,092 |
| webman | 2.2.5 | 73,282 | 72,486 | 8,301 | 6,146 |
| Hyperf | 3.2.0 | 41,652 | 41,450 | 9,380 | 6,940 |
| Symfony | 8.1.11 | 6,114 | 6,063 | 3,540 | 4,097 |
| Spiral | 3.18.2 | 3,125 | 3,153 | 2,517 | 2,663 |
| Laravel | 13.40.0 | 2,179 | 2,154 | 1,589 | 1,417 |
| Tempest | 3.21.0 | 991 | 993 | 904 | 918 |

## Findings and limits

Crab has the highest median throughput in these measured cases. Hyperf has the second-highest MySQL and validation medians; webman has the second-highest hello medians. These observations apply to the recorded deployments, workloads and machine.

**Symfony database variability:** its five trial rates span **1,920–4,636 requests/s**, with a median of **3,540**. The cause was not isolated. All trials are retained; the median is not a claim of a stable achieved rate. The website shows this caveat.

The load generator stayed below its four-CPU quota in the recorded median CPU samples (maximum across cases: 125.3%). This does not prove an unmeasured server maximum. Host activity and the shared scheduling layout remain limitations.

The tiny endpoints exclude application business logic, authentication, TLS and production traffic patterns. Database adapters and worker lifecycles differ. Closed-loop wrk latency is subject to coordinated omission. Hardware, runtime and framework versions differ from earlier website results; comparisons belong within this run.

## Verify and reproduce

```sh
python3 audit.py results/20261110T104256Z --require-full
./run.sh
```

Run those commands from the repository root. A new run creates a new timestamped result directory. The [methodology](../../README.md) documents prerequisites, workloads, limits and refresh steps.

## Evidence

- [Independent raw-log audit](audit.json)
- [Full report](summary.md) and [machine-readable summary](summary.json)
- [All measured trials](trials.json) and [all warmups](warmups.json)
- [Functional preflight checks](preflight.json)
- [Runtime and package versions](versions.json)
- [Machine and method metadata](metadata.json)
- [Resolved deployment](compose-resolved.yaml) and [source manifest](source-manifest.json)
- [Cleanup verification](cleanup-verification.json)

Individual wrk logs, resource samples and server logs are retained in this directory.
