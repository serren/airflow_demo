#!/usr/bin/env pwsh
# start.ps1
# Sets DOCKER_HOST for the current session and starts Airflow via Astro CLI.
# DOCKER_HOST is scoped to this process only — no system-wide side effects.

$env:DOCKER_HOST = "tcp://localhost:2376"

astro dev start
