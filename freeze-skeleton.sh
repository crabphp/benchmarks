#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
id=$(docker create crab-benchmark-build-spiral)
trap 'docker rm "$id" >/dev/null' EXIT
mkdir -p spiral/skeleton
docker cp "$id:/srv/app/app" spiral/skeleton/
docker cp "$id:/srv/app/app.php" spiral/skeleton/
docker cp "$id:/srv/app/public" spiral/skeleton/

python3 - <<'PYSNAPSHOT'
from pathlib import Path
for path in Path('spiral/app').rglob('*'):
    if path.is_file():
        snapshot=Path('spiral/skeleton')/path.relative_to('spiral/app')
        if snapshot.exists(): snapshot.unlink()
PYSNAPSHOT
