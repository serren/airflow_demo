import glob
import logging
import os
import shutil
import subprocess
from datetime import datetime, timedelta

import psycopg2
from airflow import DAG
from airflow.models import Connection
from airflow.operators.python import PythonOperator

from airflow.providers.dbt.cloud.operators.dbt import (
    DbtCloudRunJobOperator,
)

log = logging.getLogger(__name__)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')


def install_dependencies():
    subprocess.run(['pip', 'install', 'psycopg2-binary'], check=True)


def ingest_data():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    csv_files = glob.glob(os.path.join(DATA_DIR, '*.csv'))
    if not csv_files:
        log.info('No CSV files found in %s, nothing to ingest', DATA_DIR)
        return

    conn_cfg = Connection.get_connection_from_secrets('neon-metrics-db')
    sslmode = conn_cfg.extra_dejson.get('sslmode', 'require')
    conn = psycopg2.connect(
        database=conn_cfg.schema,
        user=conn_cfg.login,
        password=conn_cfg.password,
        host=conn_cfg.host,
        port=conn_cfg.port,
        sslmode=sslmode,
    )
    log.info('DB connected successfully')

    cursor = conn.cursor()
    copy_sql = """
        COPY metrics.metrics (component_name, from_timestamp, max_value, metric_name, min_value, to_timestamp, unit)
        FROM STDIN WITH CSV HEADER
    """

    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        log.info('Ingesting %s', filename)
        with open(csv_path, 'r') as f:
            cursor.copy_expert(copy_sql, f)
        conn.commit()
        shutil.move(csv_path, os.path.join(PROCESSED_DIR, filename))
        log.info('Moved %s to processed/', filename)

    cursor.close()
    conn.close()
    log.info('Ingestion complete: %d file(s) processed', len(csv_files))

with DAG(
    dag_id='data-quality-pipeline',
    description='Ingest CSV metrics into NeonDB',
    schedule_interval=None,
    start_date=datetime(2024, 1, 4),
    default_args=default_args,
    tags=['ingestion'],
    catchup=False,
) as dag:

    task_install = PythonOperator(
        task_id='install-dependencies',
        python_callable=install_dependencies,
    )

    task_ingest = PythonOperator(
        task_id='ingest-data',
        python_callable=ingest_data,
    )

    trigger_dbt_cloud_job_run = DbtCloudRunJobOperator(
        task_id="trigger_dbt_cloud_job_run",
        # your DBT connection name in Airflow
        dbt_cloud_conn_id="dbt-int",
        # your job ID
        job_id=70471823591098,
        check_interval=10,
        timeout=300,
    )

    task_install >> task_ingest >> trigger_dbt_cloud_job_run
