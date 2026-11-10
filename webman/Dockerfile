ARG COMPOSER_IMAGE
ARG FRANKEN_IMAGE
ARG BASE=php:8.5-cli-bookworm
FROM ${COMPOSER_IMAGE} AS composer
FROM ${FRANKEN_IMAGE} AS extensions
FROM ${BASE}
COPY --from=composer /usr/bin/composer /usr/local/bin/composer
COPY --from=extensions /usr/local/bin/install-php-extensions /usr/local/bin/install-php-extensions
RUN apt-get update && apt-get install -y --no-install-recommends unzip && install-php-extensions pcntl pdo_mysql sockets event-3.2.0 && rm -rf /var/lib/apt/lists/*
RUN cp "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"
COPY common/php.ini /usr/local/etc/php/conf.d/zz-benchmark.ini
COPY common/metadata.php /bench/metadata.php
COPY webman/ /bench/webman/
COPY webman-source/ /srv/app/
ENV COMPOSER_ALLOW_SUPERUSER=1 APP_ENV=production APP_DEBUG=false
RUN /bench/webman/setup.sh
WORKDIR /srv/app
ENTRYPOINT ["/bench/webman/entrypoint.sh"]
