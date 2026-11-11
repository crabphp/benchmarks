#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export BENCH_CONTEXT="$PWD/.work/context"
export BENCH_RESULTS="$PWD/.work/setup"
export COMPOSE_PROJECT_NAME=crab-benchmark-build
mkdir -p "$BENCH_RESULTS"
set -a
source images.env
set +a
python3 prepare.py
docker compose --progress plain build
# Freeze actual successful installations, including transitive dependencies.
for item in 'crab:crab:/srv/crab' 'webman:webman:/srv/app' 'hyperf:hyperf:/srv/app' 'symfony:symfony:/srv/app' 'spiral:spiral:/srv/app' 'laravel:laravel-octane:/srv/app' 'tempest:tempest:/srv/app' 'reactphp:reactphp:/srv/app' 'amphp:amphp:/srv/app'; do
  IFS=: read -r service folder app <<< "$item"
  # compose images lists created containers; use the built image name directly.
  id=$(docker create "${COMPOSE_PROJECT_NAME}-${service}")
  docker cp "$id:$app/composer.json" "$folder/composer.json"
  docker cp "$id:$app/composer.lock" "$folder/composer.lock"
  docker rm "$id"
done

./freeze-skeleton.sh
