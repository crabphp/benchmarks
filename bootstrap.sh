#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 resolve.py
: > images.env
for spec in 'PHP_CLI_IMAGE=php:8.5-cli-bookworm' 'FRANKEN_IMAGE=dunglas/frankenphp:php8.5-bookworm' 'MYSQL_IMAGE=mysql:8.4' 'LOADGEN_IMAGE=debian:bookworm-slim' 'COMPOSER_IMAGE=composer:latest'; do
  key=${spec%%=*}; tag=${spec#*=}
  docker pull "$tag"
  digest=$(docker image inspect "$tag" --format '{{index .RepoDigests 0}}')
  printf '%s=%s\n' "$key" "$digest" >> images.env
done
