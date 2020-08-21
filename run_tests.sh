#!/usr/bin/env bash

echo DIAGNOSTICS
cat /etc/os-release
lsb_release -a
hostnamectl
uname -r
apt list --installed
docker-compose --verbose down -v
docker-compose --verbose up -V --abort-on-container-exit --exit-code-from client "$@"
