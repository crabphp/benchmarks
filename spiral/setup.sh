#!/bin/sh
set -eu
cd /srv/app
if [ -d /bench/spiral/skeleton ]; then cp -R /bench/spiral/skeleton/. .; fi
composer install --no-dev --prefer-dist --no-interaction
if [ -d /bench/spiral/app ]; then cp -R /bench/spiral/app/. .; fi
sed -i '/DumperBootloader::class/d' app/src/Application/Kernel.php
composer dump-autoload --no-dev --classmap-authoritative
arch=$(dpkg --print-architecture)
curl -fsSL --retry 3 "https://github.com/roadrunner-server/roadrunner/releases/download/v3.0.1/roadrunner-3.0.1-linux-${arch}.tar.gz" -o /tmp/rr.tar.gz
case "$arch" in
  amd64) checksum=a6156d34a08cfdfba4934e737ed3208b11c6eab666def5c81f1b640ef43568e7 ;;
  arm64) checksum=c07f8556080b8c995c82ecc5cdf13c60c18d01da966eede848f657810b17dbd3 ;;
esac
printf '%s  /tmp/rr.tar.gz\n' "$checksum" | sha256sum -c -
tar -xzf /tmp/rr.tar.gz --strip-components=1 -C /usr/local/bin "roadrunner-3.0.1-linux-${arch}/rr"
rm /tmp/rr.tar.gz
rm -rf runtime/cache
php app.php configure
