#!/usr/bin/env bash

echo SNAPS
snap list
echo PACKAGES
apt list --installed
docker-compose --verbose down -v
docker-compose --verbose up -V --abort-on-container-exit --exit-code-from client "$@"
