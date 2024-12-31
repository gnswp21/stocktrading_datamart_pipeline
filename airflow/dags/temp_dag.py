from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.operators.mysql import MySqlOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta
import subprocess
import docker


# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
}

# Define the DAG
dag = DAG(
    'temp',
    default_args=default_args,
    schedule_interval=None,  # Trigger manually or as needed
    start_date=datetime(2024, 12, 29),
    catchup=False,
)


def run_spark_job():
    client = docker.from_env()
    container = client.containers.get("spark-master")
    result = container.exec_run(
        cmd="spark-submit /opt/bitnami/spark/myjars/constraints/check_budget.py",
        stdout=True,
        stderr=True,
    )
    if result.exit_code != 0:
        raise Exception(f"Spark job failed: {result.output.decode()}")
    print(result.output.decode())


check_table_budget = PythonOperator(
    task_id='check_table_budget',
    python_callable=run_spark_job,
    dag=dag,
)
