#!/usr/bin/env bash

echo DIAGNOSTICS
pwd
ls -la
docker-compose --verbose up -V --abort-on-container-exit --exit-code-from client "$@"
