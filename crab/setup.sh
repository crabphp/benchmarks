#!/bin/sh
set -eu
cd /srv/crab
composer install --no-dev --classmap-authoritative --prefer-dist --no-interaction
mkdir -p storage/logs
