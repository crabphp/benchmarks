ARG COMPOSER_IMAGE
ARG FRANKEN_IMAGE
ARG BASE=php:8.5-cli-bookworm
FROM ${COMPOSER_IMAGE} AS composer
FROM ${FRANKEN_IMAGE} AS extensions
FROM ${BASE}
COPY --from=composer /usr/bin/composer /usr/local/bin/composer
RUN apt-get update && apt-get install -y --no-install-recommends unzip && docker-php-ext-install -j2 pcntl pdo_mysql && rm -rf /var/lib/apt/lists/*
RUN cp "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"
COPY common/php.ini /usr/local/etc/php/conf.d/zz-benchmark.ini
COPY crab/ /bench/crab/
COPY crab-source/ /srv/crab/
COPY crab/app/ /srv/crab/
ENV COMPOSER_ALLOW_SUPERUSER=1 APP_DEBUG=false SERVER_WORKERS=2 LOG_LEVEL=error
RUN /bench/crab/setup.sh
WORKDIR /srv/crab
ENTRYPOINT ["/bench/crab/entrypoint.sh"]
