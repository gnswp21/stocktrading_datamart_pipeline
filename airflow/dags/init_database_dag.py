from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.operators.mysql import MySqlOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta
import subprocess


def check_db_status():
    """
    Check if the database exists and if the table count is less than or equal to 5.
    """
    import mysql.connector
    try:
        connection = mysql.connector.connect(
            host='db-mysql',
            user='root',
            password='1234',
        )
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES LIKE 'ctrading'")
        db_exists = cursor.fetchone() is not None

        if not db_exists:
            return 'init_db'

        cursor.execute("USE ctrading")
        cursor.execute("SHOW TABLES")
        table_count = len(cursor.fetchall())
        return 'init_db' if table_count <= 50 else 'end_process'
    finally:
        if connection:
            connection.close()


# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
}

# Define the DAG
dag = DAG(
    'database_init',
    default_args=default_args,
    description='Check and initialize MySQL database',
    schedule_interval=None,  # Trigger manually or as needed
    start_date=datetime(2024, 12, 29),
    catchup=False,
)

# Define tasks
check_db_task = BranchPythonOperator(
    task_id='check_db_status',
    python_callable=check_db_status,
    dag=dag,
)

init_db_spark_job = BashOperator(
    task_id='init_db',
    bash_command='docker exec spark-master /bin/bash '
    'spark-submit /opt/bitnami/spark/myjars/init_db.py',
    dag=dag,
)

end_process_task = DummyOperator(
    task_id='end_process',
    dag=dag,
)

# Define task dependencies
check_db_task >> [init_db_spark_job, end_process_task]
init_db_spark_job >> end_process_task
