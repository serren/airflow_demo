# Step 1 - NeonDB setup
Account setup - follow the [docs here](https://neon.tech/docs/get-started-with-neon/signing-up#step-2-onboarding-in-the-neon-console)
- visit NeonDB and create an account
- use the free tier - it will be more than enough for this practical task

**Note:** If you already have a NeonDB account, just make sure you have some free disk storage capacity to complete the task.

## Database setup

- create a database named **metrics** - follow the [docs here](https://neon.tech/docs/get-started-with-neon/signing-up#step-2-onboarding-in-the-neon-console)
  - sign-up via https://console.neon.tech/signup
  - enter project name and database name `metrics`
- create a branch named **Dev** - follow the [docs here](https://neon.tech/docs/get-started-with-neon/signing-up#step-5-create-a-dedicated-development-branch)
  - Install CLI with Brew `brew install neonctl`(MacOS) or NPM `npm install -g neonctl`  
  - Validate the installed version of `neonctl`:
    ```
    $ neonctl --version
    2.2.0
    ```
  - Authorize via `neon auth`

    ```bash
    neon auth
    INFO: Awaiting authentication in web browser.
    INFO: Auth Url: https://oauth2.neon.tech/oauth2/auth?client_id=neonctl&scope=openid....
    INFO: Saved credentials to /Users/john.snow/.config/neonctl/credentials.json
    INFO: Auth complete
    ```
  - Create your development branch `Dev`
    
## DB Connectivity Test
- use your favourite DB explorer tool (for example, DBeaver)
- get connection credentials from NeonDB - follow the [docs here](https://neon.tech/docs/get-started-with-neon/connect-neon)
- connect to NeonDB

Connection example:
- Connection String: `postgresql://metrics_owner:{PASSWORD}@ep-summer-night-a5k8vdo0.us-east-2.aws.neon.tech/metrics?sslmode=require`
- User: `metrics_owner`
- Password: {PASSWORD_FROM_CONSOLE} (See `Connection String`)
- Database: `metrics`
- URL: `jdbc:postgresql://ep-summer-night-a5k8vdo0.us-east-2.aws.neon.tech/metrics`


# Step 2 - Airflow project setup

## Prerequisites
- install [Astro CLI](https://www.astronomer.io/docs/astro/cli/install-cli) - available for all platforms, f.e. `brew install astro`(MacOS)
- validate `astro` version via the command `astro version`

## Setup Project Structure 

### Automatic initialization
* Init the basic project structure:
    ```bash
    mkdir airflow
    cd airflow
    astro dev init
    ```
* The result project structure:
    ```
    .
    ├── .astro
    │    ├── config.yaml
    │    ├── dag_integrity_exceptions.txt
    │    └── test_dag_integrity_default.py
    ├── .dockerignore
    ├── .env
    ├── .gitignore
    ├── Dockerfile
    ├── README.md
    ├── airflow_settings.yaml
    ├── dags
    │    ├── .airflowignore
    │    └── exampledag.py
    ├── include
    ├── packages.txt
    ├── plugins
    ├── requirements.txt
    └── tests
    └── dags
    └── test_dag_example.py
    ```
* Modify `Dockerfile` to allow testing of the connection
  ```
  FROM quay.io/astronomer/astro-runtime:12.2.0
  # Set environment variables
  ENV AIRFLOW__CORE__TEST_CONNECTION=Enabled
  ```
* Modify `requirement.txt` and include dbt-cloud
  ```
  apache-airflow-providers-dbt-cloud==3.10.0
  ```

### Manual initialization
* Init the project structure:
    ```bash
    # Create the main directories
    mkdir airflow
    cd airflow
    mkdir -p dags/data/processed
    mkdir include
    mkdir inputs
    mkdir plugins
    
    # the astro-runtime image version 6.0.2 from Quay.io is used as the as the base image
    #echo "FROM quay.io/astronomer/astro-runtime:6.0.2" > Dockerfile
    cat <<EOL > Dockerfile
    FROM quay.io/astronomer/astro-runtime:12.1.1
    ENV AIRFLOW__CORE__TEST_CONNECTION=Enabled
    EOL
  
    # The requirements.txt has to specify a DBT Cloud integration dependency
    echo "apache-airflow-providers-dbt-cloud==2.3.1" > requirements.txt
    
    # Create .dockerignore with the recommended content
    cat <<EOL > .dockerignore
    .astro
    .git
    .env
    airflow_settings.yaml
    logs/
    EOL
    
    # Create .gitignore with the recommended content
    cat <<EOL > .gitignore
    .astro/
    .env
    airflow_settings.yaml
    dags/data/
    dags/__pycache__/
    EOL
    
    # Create empty files
    touch .env packages.txt
    ```

* The result project structure:
    ```
    .
    ├── .dockerignore       # for Docker builds
    ├── .env                # for env variables, may be empty
    ├── .gitignore          # the usual, see an example below
    ├── Dockerfile          # the Airflow image, see the details below
    ├── dags                # this host your Airflow code and data
    │   └── data
    │       └── processed
    ├── include             # just keep empty
    ├── inputs              # just keep empty
    ├── packages.txt        # just keep empty
    ├── plugins             # just keep empty
    └── requirements.txt    # extra dependencies for Airflow, see the details below
    ```

## Run Airflow
- put a sample DAG to the `dags` folder - for example, use [this snippet](https://github.com/sungchun12/airflow-dbt-cloud/blob/main/dags/example-dag.py)
- from the root folder of you project, execute the following command: `astro dev start`
- wait until all the images are downloaded and Airflow is started - may take up to 10 minutes for the first time
- test that Airflow admin UI is available at `localhost:8080`
- try running your sample DAG
- keep in mind the following [Astro CLI command reference](https://www.astronomer.io/docs/astro/cli/reference)

# Step 3 - Airflow-NeonDB integration
* Create a role for Airflow:
  - open [NeonDB SQL editor](https://neon.tech/docs/get-started-with-neon/query-with-neon-sql-editor) - make sure to choose your Dev branch and metrics DB
  - create a **airflow-agent** role
  - make sure to grant it the `CREATE` privileges on the metrics schema
    ```sql
    CREATE ROLE "airflow-agent" WITH PASSWORD 'agent_password#007' LOGIN CREATEDB CREATEROLE;
    CREATE SCHEMA IF NOT EXISTS metrics;
    GRANT USAGE ON SCHEMA metrics TO "airflow-agent";
    GRANT CREATE ON SCHEMA metrics TO "airflow-agent";
    ```

* Create a DB connection in Airflow
  - recap or learn about connection management in Airflow - [the docs](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html)
  - follow [this guide](https://debruyn.dev/2024/connecting-neon-with-dbt-cloud/) to find out how to properly create a NeonDB connection
      - the DB login will be the name of the role - "airflow-agent"
  - test the connection from Airflow UI and make sure no errors pop up

* Prepare a test data model
- The windowed metrics dataset represents an aggregation of the metrics stream in windows of 5-minute length. They can be viewed as the following JSON document:
  ```json
  {
    "componentName": "user-service", // the component produced the event
    "metricName": "cpu-usage", // the name of the metric
    "unit": "percent", // measurement unit
    "minValue": 10, // measurement values: min
    "maxValue": 23, // measurement values: max
    "fromTimestamp": "2021-09-09T12:15:02.001Z", // the time which the window is computed for
    "toTimestamp": "2021-09-09T12:15:07.001Z"
  }
  ```
- learn about the test data model [here](../../aws/DATA_MODEL.md) - the "Windowed metrics" section

* Create an `init-db` DAG in Airflow
  - use the following Python code or similar
    ```python
    import psycopg2
    import subprocess
    from datetime import datetime
    
    from airflow.operators.python import PythonOperator
    from airflow.operators.bash import BashOperator
    from airflow import DAG
    from airflow.models import Connection
    
    def install_dependencies():
        subprocess.run(['pip','install','psycopg2'])
    
    def create_database_with_tables():
       print('Create dependencies....')
       connectionConfig = Connection.get_connection_from_secrets("neon-metrics-db")
       print(f"Connection config: host={connectionConfig.host}, schema={connectionConfig.schema}, "
            f"user={connectionConfig.login}, password={connectionConfig.password}")
        conn = psycopg2.connect(database=connectionConfig.schema,user=connectionConfig.login,password=connectionConfig.password,
                                host=connectionConfig.host,port=connectionConfig.port,sslmode=connectionConfig.extra_dejson["sslmode"])
        print('DB connected successfully')
    
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE {connectionConfig.schema}.metrics (
              component_name text,
              from_timestamp text,
              max_value double precision,
              metric_name text,
              "min_value" double precision,
              to_timestamp text,
              unit text
            );
        """)
    
        conn.commit()
        conn.close()
    
    database_init_dag = DAG(dag_id='database-init',
                             description='DAG for initialising a PostgreSQL database',
                             schedule_interval=None,
                             start_date=datetime(2024,1,4))
    
    task0 = PythonOperator(task_id='Install-dependencies',
                           python_callable=install_dependencies,
                           dag=database_init_dag)
    task1 = PythonOperator(task_id='Create-Database-With-Tables',
                           python_callable=create_database_with_tables,
                           dag=database_init_dag)
      ```
- examine the code
    - notice the use of [connections API](https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/models/connection/index.html) for getting the DB URL and credentials securely
    - replace `neon-metrics-db` with the actual name of your DB connection in Airflow
    - to avoid automatic scheduling, `schedule_interval=None` is specified
- run the DAG and make sure the new table appears in NeonDB
  ```sql
  SELECT tablename
  FROM pg_tables
  WHERE schemaname = 'metrics';
  ```

# Step 4 - data ingestion setup

## Prepare test data
- generate the test data
    - find out how to run the test data generator [here](../../aws/TEST_DATA.md) - the "Basic usage" and "CSV-formatted metrics" sections
    - run the test data generator from [here](../../aws/materials/test-data-generator-prebuilt) - use or customise the `metrics-batch.json` task config, f.e. ` java -jar test-data-generator-1.0.0-all.jar metrics-batch.json`
- copy the resulting data from `test-output` to the `dags/data` folder of your Airflow project

## Implement ingestion
- create a new DAG - `data-quality-pipeline`
    - add a step for installing Python dependencies
    - add a step which
        - connects to the DB - see the sample code from step 3
        - iterates over the files in the `dags/data` folder
        - copies each file to the DB, commits, and moves the file to the `processed` folder
    - hints
        - use the [COPY statement](https://www.postgresql.org/docs/current/sql-copy.html) with [this from the Psycopg library](https://www.psycopg.org/docs/cursor.html#cursor.copy_expert)
        - do not forget to commit the transaction
        - use [this](https://medium.com/@rajatbelgundi/efficient-etl-cleaning-transforming-and-loading-csv-data-in-postgresql-with-airflow-in-a-0bf062a0ed41) to see an example of how to upload CSVs to PostgreSQL
- run the DAG and make sure the data appears in NeonDB by querying it there. Both csv files should be imported.
  ```sql
  set schema 'metrics';

  select component_name, count(1) as "amount" from metrics
  group by component_name;
  ```

# Step 5 - DBT model setup

## Create a role for DBT
  - make sure to choose your Dev branch and metrics DB
  - create a **dbt-agent-role** role
  - make sure to grant it the CREATE privileges on the metrics schema
    ```sql
    CREATE ROLE "dbt-agent" WITH PASSWORD 'dbtagent#password' LOGIN CREATEDB CREATEROLE;
    GRANT USAGE ON SCHEMA metrics TO "dbt-agent";
    GRANT CREATE ON SCHEMA metrics TO "dbt-agent";
    ```

## Set up a DBT Cloud project

**PITFALL - DBT Cloud API access**
- If you have an existing DBT Cloud account, you'll likely have to create a new one because the task below requires API access. But the API access is
available either as part of a 14-day trial or as part of a paid plan.

Steps to follow:
  - create a free [DBT Cloud account](https://www.getdbt.com/product/dbt-cloud)
  - on the connection configuration step pay attention to the following
    - the host will be the full endpoint name from NeonDB including the `ws.neon.tech` postfix
    - the port must be 5432
    - in the advanced options, make sure to specify the database where the task data will be held + ensure the DB role created for DBT has access to that database
  - **important**: it's recommended to use a managed Git repository
  - create a **development** environment - this is where you will write DBT code
    - follow [the docs](https://docs.getdbt.com/docs/deploy/deploy-jobs)
    - choose any sensible name
    - as the username, use name of the role created for DBT above
    - as the password, use the password specified during the role creation
    - make sure to choose the correct DB schema
    - choose the connection created above
    - make sure to specify `sslmode: require` in the extended attributes
  - if you didn't create a deployment environment during the project creation
    - follow [the docs](https://docs.getdbt.com/docs/deploy/deploy-jobs)
    - create a **deployment** environment - this is where the `main` branch will be deployed (by default)
    - use settings similar to the development environment
  - in your DBT profile > Credentials > configure Development Credentials (may be the same as used for the environments above)
  - initialise a project
      - familiarise with the [DBT project structure](https://docs.getdbt.com/docs/build/projects)
      - open your project in the [DBT Cloud IDE](https://docs.getdbt.com/docs/cloud/dbt-cloud-ide/develop-in-the-cloud) and explore it
      - **PITFALL**: If the cloud IDE fails to start
        - option A - make sure your project has a [managed Git repository](https://docs.getdbt.com/docs/collaborate/git/managed-repository) attached to it
        - option B - or connect your own [GitHub/GitLab repo](https://docs.getdbt.com/docs/cloud/git/git-configuration-in-dbt-cloud)

* Create a DBT model
  - read about [models](https://docs.getdbt.com/docs/build/models) and [SQL models](https://docs.getdbt.com/docs/build/sql-models) in particular
  - open your DBT project and create a development branch
  - add a model that is based on a view of the metrics table
  - commit the branch
  - merge to main - this will automatically promote your code to the deployment environment
  - **PITFALL**: make sure to click "Save" on each file you create or modify in the DBT Cloud IDE - otherwise, the changes may be lost on commit

* Create a DBT job
  - read about [jobs](https://docs.getdbt.com/docs/deploy/jobs)
  - create a job that runs on the deployment environment
  - run the job and make sure it completes successfully

* Create a [data test](https://docs.getdbt.com/docs/build/data-tests)
  - read about [data tests](https://docs.getdbt.com/docs/build/data-tests)
  - switch to the `development` branch
  - add a test that validates min/max values against some threshold
      - make sure the test fails if the threshold is set to some high value - run the job to check that
      - rollback
      - run the job again and ensure the test passes

# Step 6 - Airflow-DBT integration

- create a [DBT service account token](https://docs.getdbt.com/docs/dbt-cloud-apis/service-tokens) for Airflow
    - make sure to specify the `Job admin` permissions
    - **PITFALL:** do not forget to copy the token right after the creation — it will not be visible afterwards
- add a connection in Airflow UI
    - choose `dbt Cloud` as the connection type
    - look up the domain/account values from the URL you used to work with your DBT Cloud project
    - **PITFALL:** do not forget to specify your tenant in the Airflow connection settings (this is the host part of your DBT Cloud project HTTP URL)
    - For more details:
      - [Create a dbt Cloud connection in Airflow](https://www.astronomer.io/docs/learn/connections/dbt-cloud)
      - [Airflow and IDB Cloud](https://docs.getdbt.com/guides/airflow-and-dbt-cloud?step=11)
- add another step to your `data-quality-pipeline` DAG from step 4
    - add the following import
      ```python
      from airflow.providers.dbt.cloud.operators.dbt import (
         DbtCloudRunJobOperator,
      )
      ```
    - add the following code
      ```python
      trigger_dbt_cloud_job_run = DbtCloudRunJobOperator(
             task_id="trigger_dbt_cloud_job_run",
             # your DBT connection name in Airflow
             dbt_cloud_conn_id="dbt-quality-pipeline",
             # your job ID
             job_id=123,
             check_interval=10,
             timeout=300,
         )
      ```
- run the DAG and make sure the DBT job is successfully triggered

# Optional step - automatic Airflow trigger
- explore Airflow sensors - special tasks that listen for external events - e.g. [file system](https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/file.html#howto-operator-filesensor)
- use a sensor to make your `data-quality-pipeline` DAG run every time some files change in the `dags/data` folder

# Exam/review with the mentor
To accept this task, it's mandatory to have a demo of the whole data pipeline running end-to-end.
Optionally, it's possible to have a separate offline code review session, if necessary.

**The demo** may be **either a video recording (recommended)** or a **live session with the mentor**.

The following steps must be included:
1. An empty *metrics* table is demonstrated in the _NeonDB database_.
2. The _test data generator_ is run to create a CSV file with fresh metrics.
3. Open the file and copy a random row to a text editor of choice. Also, note the number of rows generated.
4. Copy the CSV file to the `dags/data` folder.
5. Run the data-quality-pipeline in _Airflow UI_.
   1. The run should be a success.
   2. Show the status details of the run - it should be visible that there are steps for data ingestion and for data quality checks.
6. Show the NeonDB *metrics* table and
   1. confirm that the number of rows correspond to the CSV generated above
   2. make a `SELECT` query to confirm that the row chosen on step 3 is ingested
7. Open the *DBT Cloud* and navigate to the jobs. Show that the data-quality job has been run recently and is a success.
8. Show the data-quality job logs to confirm that it ran at least one data test.
