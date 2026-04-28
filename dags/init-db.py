import logging
import psycopg2
import subprocess
from datetime import datetime

from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow import DAG
from airflow.models import Connection

log = logging.getLogger(__name__)

def install_dependencies():
    subprocess.run(['pip','install','psycopg2'])

def create_database_with_tables():
    log.info('Creating database tables...')
    connectionConfig = Connection.get_connection_from_secrets("neon-metrics-db")
    log.info(f"Connection config: host={connectionConfig.host}, schema={connectionConfig.schema}, "
             f"user={connectionConfig.login}")
    sslmode = connectionConfig.extra_dejson.get("sslmode", "require")
    conn = psycopg2.connect(database=connectionConfig.schema,user=connectionConfig.login,password=connectionConfig.password,
                            host=connectionConfig.host,port=connectionConfig.port,sslmode=sslmode)
    log.info('DB connected successfully')

    cursor = conn.cursor()
    log.info('Executing CREATE TABLE...')
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
    log.info('Table created and transaction committed')
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

task0 >> task1
