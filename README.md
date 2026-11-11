# PHP framework and HTTP server benchmarks

A public, independently runnable comparison of seven frameworks and two async HTTP libraries for the CrabPHP website. Every PHP runtime is **8.5**. Frameworks and libraries use the published stable releases pinned in [`sources.json`](sources.json); dependencies stay frozen for repeatability.

## Reference results

[Audited reference run: 10 November 2026](results/20261110T104256Z/README.md) — PHP 8.5.12, 140 trials and 140 warmups, zero errors across 44.8 million measured responses. It includes full trial ranges, latency, memory, exact versions, configuration and limitations. Symfony’s database results have substantial variability, disclosed alongside its median.

[Audited ReactPHP/AMP supplement: 11 November 2026](results/20261111T055316Z/README.md) — twenty measured trials and twenty warmups for the two added library rows (Hello and MySQL at 64 connections), zero errors across 5.4 million measured responses. The website retains the original seven framework rows and separately dates and links the additions; these were not one simultaneous comparison.

## Run

Install **Docker Engine or Docker Desktop with Compose v2**, **Python 3.12+**, and Bash. Allow at least four logical CPUs, 8 GiB available RAM and 12 GiB free disk. Linux, macOS and Windows with WSL2 can run the harness; Linux amd64 is the reference environment. No host PHP, Composer, database, sibling repository, or credentials are needed.

```sh
git clone https://github.com/crabphp/benchmarks.git
cd benchmarks
./run.sh
```

First builds download and compile the runtimes. Watch the terminal for progress. The full measurement takes about **70 minutes**, plus builds and server restarts. `results/<UTC timestamp>/summary.md` and `summary.json` contain the report. `Ctrl+C` stops the run and cleans up this run's containers and disposable database volume. Existing containers and databases are not touched. Ports 23101–23109 and 23306 must be free; all host bindings use loopback.

For a quick setup check:

```sh
BENCH_WARMUP=1 BENCH_DURATION=2 BENCH_TRIALS=1 ./run.sh
```

Smoke runs must not supply the website table. Optional `BENCH_SERVICES=crab,laravel`, `BENCH_CASES=hello,db` and `BENCH_CONNECTIONS=64` select subsets and mark `full_method: false`; they never claim a complete comparison. A five-trial two-library supplement can be published separately as described below. Do not run two copies from the same checkout.

## What is measured

| Framework / server | Deployment | Application workers |
| --- | --- | ---: |
| Crab | Native PHP server, select loop, PDO | 2 |
| webman | Workerman, ext-event, Illuminate database | 2 |
| Hyperf | Swoole coroutine HTTP, connection pool | 2 |
| Symfony | FrankenPHP worker mode, Doctrine DBAL | 2 |
| Spiral | RoadRunner, Cycle DBAL | 2 |
| Laravel | Octane with FrankenPHP, Illuminate database | 2 |
| Tempest | FrankenPHP worker mode, Tempest database | 2 |
| ReactPHP HTTP | Native CLI, ext-event, react/mysql | 2 |
| AMP HTTP Server | Native CLI, Revolt ext-event, amphp/mysql | 2 |

ReactPHP HTTP and AMP HTTP Server are **HTTP libraries, not full application frameworks**. Their adapters add routing (FastRoute and AMP Router respectively) and explicit PHP validation. Each uses two supervised forked workers with `SO_REUSEPORT`, and up to ten persistent native async MySQL connections per worker (600-second idle timeout). ReactPHP distributes queries round-robin across ten lazy queued connections; AMP uses its native bounded connection pool. Neither uses blocking PDO inside its event loop. The common disposable MySQL account uses `mysql_native_password` because react/mysql 0.6 does not support MySQL 8's default authentication; this applies to every contender, not just ReactPHP. This compatibility setting is not production deployment advice.

These are **framework/server plus deployment** comparisons: server, middleware, database access and worker lifecycle differences affect results. They are small synthetic workloads, not a universal framework ranking or an application capacity estimate.

- `GET /hello`: JSON `{"message":"Hello, world"}`; 64 and 256 persistent connections.
- `GET /users/{id}`: one indexed MySQL read from a common 10,000-row fixture, returned as JSON; 64 connections.
- `POST /users`: parse JSON, use each framework's validator (or explicit checks for HTTP libraries) for name length 1–100, email format and integer age 18–120, return the input with status 201; 64 connections. This does not write to the database. Explicit strict type checks supplement validators that coerce numeric strings.

Requests cycle through 10,000 variants, including request headers and query parameters. No response cache, pipelining, TLS or static hello shortcut is used. Each request traverses a router. Preflight verifies exact representative database values, valid and invalid validation boundaries, persistent connections, actual PHP 8.5, OPcache, JIT and production settings. The load generator checks every response status and body; database/validation fields must match the fixture's internally consistent values.

## Method and fairness

- Same limits: **2 CPU quota units and 2 GiB RAM per application**, no extra swap. MySQL has 2 CPUs/2 GiB; wrk has 4 CPUs/512 MiB. Exactly one application is running during load. Database and load generator are shared. All traffic follows the same container network path.
- CPU quotas limit scheduling time; they do **not** reserve physical cores. No CPU affinity is required, allowing rootless Docker. Shared host activity, database and client competition can affect measurements. Metadata records host load and other running containers. Use an otherwise idle dedicated machine for strong performance conclusions.
- Production PHP configuration, 256 MiB OPcache, disabled timestamp checks, **JIT off for every contender**, Composer `--no-dev --classmap-authoritative`, debug disabled. FrankenPHP is ZTS; CLI runtimes are NTS. Actual versions and loaded settings are recorded.
- Fresh application containers per case. Five rounds rotate contender order. Every trial gets **5 seconds warmup followed by 15 seconds measurement**, with four wrk threads. Keep-alive is enabled. Latency is wrk's closed-loop latency and is subject to coordinated omission; it is not a fixed arrival rate SLA test.
- Median throughput and range, median trial p50/p99, total errors, sampled CPU and peak container memory are reported. No fastest-trial selection or outlier removal. Peak container memory includes warmup and startup. Memory sampling includes processes and charged cache, not just PHP heap.
- Errors remain visible and make the run invalid for website publication. Every trial and warmup is retained. Setup failures stop the suite; a missing framework is never silently omitted.

Laravel caches configuration, events, routes and views; Octane retains its 500-request recycling policy. Symfony warms production caches and OPcache preloading. Hyperf caches scanning/DI and disables request-count recycling to preserve keep-alive connections. Spiral caches configuration/tokenization and does not recycle by request count. webman disables the development monitor and retains controller reuse off. Tempest caches discovery and uses its native worker application; its API routes disable session, cookie and CSRF middleware, as the other stateless fixtures do. PHP uses its automatic garbage collector. Crab uses its published skeleton and published framework package, without local source patches.

## Audit the evidence

Every run includes:

- `sources.json` (copied into metadata): framework versions, skeleton commits and SHA-256 checksums.
- `source-manifest.json`: hashes of the complete build context; `harness/` retains the scripts and configuration used.
- `compose-resolved.yaml`, image metadata and container inspections: effective resource and network configuration.
- `versions.json`, `preflight.json`: installed package versions/references, runtime settings and functional checks.
- `warmups.json`, `trials.json`, individual wrk logs, resource samples and server logs.
- `metadata.json`: host, architecture, CPU, Docker, timing, settings, completeness and validity.
- `cleanup.log`: cleanup results. An interrupted run lacks a completed valid summary.

The full application overlays, MySQL fixture and workload checker live here. Fork the repository, inspect or change them, and publish your own result directory with an explanation of changes. Results on different hardware are not directly comparable.

Recompute the report audit independently:

```sh
python3 audit.py results/<timestamp> --require-full
```

`update-site.py results/<timestamp> --site ../crabphp-site` replaces the whole table only after that audit passes. It requires all nine contenders, all four cases, all five trials and zero errors. Historical seven-framework runs remain independently auditable.

### Add only the two HTTP libraries

Keep the seven existing framework measurements and measure only the two new table rows (about eight minutes, plus builds):

```sh
BENCH_SERVICES=reactphp,amphp BENCH_CASES=hello,db BENCH_CONNECTIONS=64 ./run.sh
python3 audit.py results/<library-timestamp> --require-libraries
python3 add-libraries.py results/<library-timestamp> --baseline results/20261110T104256Z --site ../crabphp-site
```

The supplemental audit requires exactly ReactPHP and AMP, Hello and MySQL at 64 connections, five 15-second trials with five-second warmups, complete functional preflights and zero errors. It rejects smoke runs and cannot pass `--require-full`. The updater audits both sources, checks matching PHP/image pins and host/CPU, verifies the existing seven website rows match the baseline, then preserves those rows verbatim. Dates and raw-result links disclose the separate runs rather than presenting them as one simultaneous comparison. The supplemental MySQL account authentication compatibility setting is disclosed above; the historical baseline remains unchanged.

## Refresh dependencies (maintainers)

Ordinary `./run.sh` uses committed source checksums, image digests and Composer locks. It never updates packages. The initial source comparison was adapted from `crabphp/framework/benchmarks/frameworks` (MIT); the old PHP 8.4 measurements are not reused.

```sh
# Refresh latest stable source releases and base image digests explicitly:
./bootstrap.sh
# Remove old locks/manifests for a deliberate dependency refresh first.
./build.sh
# Review and commit new sources.json, images.env, Dockerfiles and all locks.
./run.sh
```

The generated Spiral starter source is committed in `spiral/skeleton/`, so lockfile installs do not need to run its interactive project generator. Adapter code is in `spiral/app/`.

Spiral’s upstream installer requires a prerelease gRPC client dependency; the framework itself remains the latest stable release. Its exact transitive version is visible in the lock and run metadata.

To add or refresh only the HTTP library source pins without changing existing framework versions, run `python3 resolve.py --only reactphp amphp`, then deliberately regenerate their Composer locks. Do not refresh the seven existing graphs just to add contenders.

Run harness regression tests with `python3 -m unittest discover -s tests -v` and validator checks with `php tests/async-validation.php`; fixture integration checks run automatically before measurements.

Runtime extensions and RoadRunner downloads are pinned in Dockerfiles/setup scripts, with RoadRunner checksums for amd64 and arm64. Review those pins when refreshing. Debian OS packages are installed from distribution repositories rather than a dated snapshot; image digests and recorded image/package metadata document that remaining reproducibility limit.

## Engine maintainer tools

Optional [engine diagnostics](engine/README.md) retain the request-path CPU and
long-running HTTP/WebSocket soak harnesses from the framework. They can target
a local framework checkout and require host tools; they are separate from the
independently runnable published-release comparison above and do not supply
website ranking results.

## License

MIT. See [LICENSE](LICENSE). Upstream frameworks and runtimes retain their own licenses.
