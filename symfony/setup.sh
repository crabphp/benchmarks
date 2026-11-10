#!/bin/sh
set -eu
export COMPOSER_ROOT_VERSION=8.1.99
cd /srv/app
cp -R /bench/symfony/recipe/. /srv/app/
composer install --no-dev --classmap-authoritative --prefer-dist --no-interaction --no-scripts
cp -R /bench/symfony/app/. /srv/app/
composer dump-autoload --no-dev --classmap-authoritative
printf 'APP_ENV=prod\nAPP_SECRET=benchmark-secret\nDEFAULT_URI=http://symfony:8080\nDATABASE_URL=mysql://bench:bench@mysql:23306/benchmark\n' > .env
composer dump-env prod
php bin/console cache:clear --env=prod --no-debug
php bin/console cache:warmup --env=prod --no-debug
