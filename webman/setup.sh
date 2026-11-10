#!/bin/sh
set -eu
cd /srv/app
composer install --no-dev --classmap-authoritative --prefer-dist --no-interaction --no-scripts
cp -R /bench/webman/app/. .
composer dump-autoload --no-dev --classmap-authoritative --no-scripts
