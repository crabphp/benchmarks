#!/bin/sh
set -eu
cd /srv/crab
exec php cua start --address=tcp://0.0.0.0:8080
