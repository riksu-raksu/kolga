#!/usr/bin/env bash

docker-compose down -v
whoami; groups
sudo usermod -a -G docker vsts_azpcontainer
bash -lic "whoami; groups"
docker-compose --verbose up -V --abort-on-container-exit --exit-code-from client "$@"
