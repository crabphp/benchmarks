#!/bin/sh
set -eu
cd /srv/app
composer install --no-dev --classmap-authoritative --prefer-dist --no-interaction --no-scripts
cp -R /bench/tempest/app/. .
# Remove the starter's example route and sqlite configuration.
rm -f app/HomeController.php app/database.php
composer dump-autoload --no-dev --classmap-authoritative --no-scripts
php tempest discovery:generate
