Overview
========

Welcome to Astronomer! This project was generated after you ran 'astro dev init' using the Astronomer CLI. This readme describes the contents of the project, as well as how to run Apache Airflow on your local machine.

Project Contents
================

Your Astro project contains the following files and folders:

- dags: This folder contains the Python files for your Airflow DAGs. By default, this directory includes one example DAG:
    - `example_astronauts`: This DAG shows a simple ETL pipeline example that queries the list of astronauts currently in space from the Open Notify API and prints a statement for each astronaut. The DAG uses the TaskFlow API to define tasks in Python, and dynamic task mapping to dynamically print a statement for each astronaut. For more on how this DAG works, see our [Getting started tutorial](https://www.astronomer.io/docs/learn/get-started-with-airflow).
- Dockerfile: This file contains a versioned Astro Runtime Docker image that provides a differentiated Airflow experience. If you want to execute other commands or overrides at runtime, specify them here.
- include: This folder contains any additional files that you want to include as part of your project. It is empty by default.
- packages.txt: Install OS-level packages needed for your project by adding them to this file. It is empty by default.
- requirements.txt: Install Python packages needed for your project by adding them to this file. It is empty by default.
- plugins: Add custom or community plugins for your project to this file. It is empty by default.
- airflow_settings.yaml: Use this local-only file to specify Airflow Connections, Variables, and Pools instead of entering them in the Airflow UI as you develop DAGs in this project.

Local Development (Windows + Podman)
=====================================

This project runs on Windows via Podman (WSL backend) instead of Docker Desktop.
Ports are fixed via `docker-compose.override.yml`:

| Service     | URL / connection string                          | Credentials        |
|-------------|--------------------------------------------------|--------------------|
| Airflow UI  | http://localhost:6563                            | admin / admin      |
| Postgres    | postgresql://postgres:postgres@localhost:18741   | postgres / postgres|

First-time setup
----------------

Run once after cloning the repo or after recreating the Podman machine:

    .\setup-astro.ps1

This script will:
1. Check that the `astro-machine` Podman machine exists and is running
2. Fix systemd directory ownership inside the machine
3. Install and enable the `podman-api-tcp` systemd service (auto-starts Podman API
   on port 2376 every time the machine boots)

After setup completes, proceed to the regular start below.

Regular start
-------------

    .\start.ps1

This script sets `DOCKER_HOST=tcp://localhost:2376` for the current session only
and runs `astro dev start`. No system-wide environment variables are modified.

Stopping
--------

    $env:DOCKER_HOST = "tcp://localhost:2376"
    astro dev stop

Deploy Your Project Locally (original)
=======================================

Start Airflow on your local machine by running 'astro dev start'.

This command will spin up five Docker containers on your machine, each for a different Airflow component:

- Postgres: Airflow's Metadata Database
- Scheduler: The Airflow component responsible for monitoring and triggering tasks
- DAG Processor: The Airflow component responsible for parsing DAGs
- API Server: The Airflow component responsible for serving the Airflow UI and API
- Triggerer: The Airflow component responsible for triggering deferred tasks

When all five containers are ready the command will open the browser to the Airflow UI at http://localhost:8080/. You should also be able to access your Postgres Database at 'localhost:5432/postgres' with username 'postgres' and password 'postgres'.

Note: If you already have either of the above ports allocated, you can either [stop your existing Docker containers or change the port](https://www.astronomer.io/docs/astro/cli/troubleshoot-locally#ports-are-not-available-for-my-local-airflow-webserver).

Deploy Your Project to Astronomer
=================================

If you have an Astronomer account, pushing code to a Deployment on Astronomer is simple. For deploying instructions, refer to Astronomer documentation: https://www.astronomer.io/docs/astro/deploy-code/

Contact
=======

The Astronomer CLI is maintained with love by the Astronomer team. To report a bug or suggest a change, reach out to our support.
