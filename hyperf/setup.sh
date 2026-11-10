#!/bin/sh
set -eu
cd /srv/app
composer install --no-dev --classmap-authoritative --prefer-dist --no-interaction --no-scripts
cp -R /bench/hyperf/app/. .
composer dump-autoload --no-dev --classmap-authoritative --no-scripts
SCAN_CACHEABLE=false php bin/hyperf.php list > /dev/null
