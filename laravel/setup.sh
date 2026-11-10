#!/bin/sh
set -eu
mode=$1
export COMPOSER_ROOT_VERSION=13.11.0
cp -R /bench/laravel/app/. /srv/app/
cd /srv/app
composer install --no-dev --classmap-authoritative --prefer-dist --no-interaction
if [ "$mode" = octane ]; then
    ln -s /usr/local/bin/frankenphp /srv/app/frankenphp
    php artisan octane:install --server=frankenphp --no-interaction
fi
php artisan config:cache
php artisan event:cache
php artisan route:cache
php artisan view:cache
