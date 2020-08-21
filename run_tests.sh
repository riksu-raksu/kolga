#!/usr/bin/env bash

docker-compose --verbose down -v
docker-compose --verbose up -V --abort-on-container-exit --exit-code-from client "$@"
