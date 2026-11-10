#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
for program in docker python3; do
  command -v "$program" >/dev/null || { echo "Install $program first (see README.md)." >&2; exit 1; }
done
docker compose version >/dev/null
docker info >/dev/null
export BENCH_CONTEXT="$PWD/.work/context"
export BENCH_RESULTS="${BENCH_RESULTS:-$PWD/results/$(date -u +%Y%m%dT%H%M%SZ)}"
export COMPOSE_PROJECT_NAME="crab-benchmark-$(date -u +%Y%m%d%H%M%S)-$$"
mkdir -p "$BENCH_RESULTS"
set -a
source images.env
set +a
cleanup() {
  code=$?
  trap - EXIT INT TERM
  docker compose logs --no-color > "$BENCH_RESULTS/final-server.log" 2>&1 || true
  docker compose down --volumes --remove-orphans > "$BENCH_RESULTS/cleanup.log" 2>&1 || true
  printf 'Results: %s\n' "$BENCH_RESULTS"
  exit "$code"
}
trap cleanup EXIT
trap 'exit 130' INT TERM
python3 -I prepare.py
docker compose config > "$BENCH_RESULTS/compose-resolved.yaml"
docker compose --progress plain build 2>&1 | tee "$BENCH_RESULTS/build.log"
python3 -I runner.py 2>&1 | tee "$BENCH_RESULTS/run.log"
python3 -I audit.py "$BENCH_RESULTS"
