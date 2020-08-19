#!/usr/bin/env bash

docker-compose down -v
sudo chmod -R 777 ./tests
whoami
pwd
ls -l tests
ls -l tests/registry
ls -l tests/registry/certs
sudo docker-compose --verbose up -V --abort-on-container-exit --exit-code-from client "$@"
