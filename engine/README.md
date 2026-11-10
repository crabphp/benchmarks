# Engine maintainer tools

Optional diagnostics for changes to Crab's engine, separate from the published
PHP 8.5 framework comparison at the repository root. These tools were retained
from `crabphp/framework` at commit
`917a2f23c86dd458673e3dc8d1ec63691fd58029`; old research, patches and results
remain in that repository's Git history. They are not website ranking evidence.

## Setup

Use a Unix-like host with PHP 8.4 or newer and Composer. The soak also needs
`wrk`, Node.js, `ps`, and either Linux `/proc` or `lsof`. No Python or Node
packages are required. Run the following from this benchmark repository:

```sh
set -e
git clone https://github.com/crabphp/framework.git .work/framework
composer install --working-dir=.work/framework --no-interaction --no-progress
export CRAB_FRAMEWORK="$PWD/.work/framework"
```

Alternatively, set `CRAB_FRAMEWORK` to an absolute path to the installed
framework checkout being changed. With no override, the PHP tools use
`.work/framework` in this repository. The main Docker comparison still needs
no host PHP, Composer or framework checkout and always uses published releases.

## Request-path CPU cost

```sh
php -d opcache.enable_cli=1 -d opcache.jit=tracing -d opcache.jit_buffer_size=128M \
  engine/request-path.php --iterations=300000 --trials=5 --http-response=fresh
```

The tool sends rotating browser-sized requests over a socket pair and reports
user-mode CPU per request, subtracting the same stream calls without the
engine. It reports the minimum over trials, not a throughput or latency result.
It calls the connection's private read turn and is intentionally engine-internal.
It measures the engine alone, not framework routing or middleware; measure the
corresponding framework path separately when reporting its added cost.

`--source=/absolute/path/to/src/Engine` selects another engine source snapshot
while using the configured checkout's Composer dependencies. Alternate the
before/after order, use the same PHP settings, and record both revisions,
commands, environment, errors and limitations with the results. `reuse` and
`string` are alternative `--http-response` modes; `fresh` creates a new response
for each request.

## Long-running stability

```sh
python3 engine/soak.py --label=overnight --minutes=480
```

The soak uses the configured framework checkout, starts only its own loopback
HTTP and WebSocket servers, and stops them afterward. It cycles persistent
requests, connection-close requests, bodies, streamed megabyte responses,
validated WebSocket echoes, and malformed or abandoned clients. After quiet
periods it samples resident memory and open descriptors. Tracing JIT is on by
default; `--jit=off` disables it. Reports go to
`engine/results/soak-<label>.json`. Use a simple filename for the label.

A short run is only a setup check. Hours are needed to look for a memory trend;
this is not a throughput benchmark or production capacity qualification. The
inherited HTTP load checks record socket errors but do not currently fail on
those alone; inspect them as well as the report's final status. Retain reports
with source revisions and machine/runtime details when reporting findings.

`server.php` is the shared HTTP/WebSocket fixture. `websocket.mjs` is its
standalone, dependency-free echo checker. The fixture also accepts `--source`
for engine snapshots. Do not run load generation alongside the root comparison
or other benchmarks; the soak takes the historical host-wide engine lock, not
the Docker comparison's run lock.
