from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.operators.mysql import MySqlOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta
import subprocess


# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    # "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    "transfer_db_to_big_dag",
    default_args=default_args,
    description="A DAG to run transfer_db_to_big.py every 30 minutes",
    schedule_interval="*/30 * * * *",  # Cron expression for every 30 minutes
    start_date=datetime(2024, 1, 1),  # Replace with the desired start date
    catchup=False,
)

# set spark-submit options
PACKAGES = '--packages  com.amazon.deequ:deequ:2.0.7-spark-3.5,mysql:mysql-connector-java:8.0.33'
JARS = '--jars myjars/packages_jars/spark-bigquery-with-dependencies_2.12-0.41.1.jar'


check_table_budget = BashOperator(
    task_id='check_table_budget',
    bash_command='docker exec spark-master /bin/bash '
    f'spark-submit {PACKAGES} {JARS} /opt/bitnami/spark/myjars/constraints/check_budget.py',
    dag=dag,
)

check_table_customer = BashOperator(
    task_id='check_table_customer',
    bash_command='docker exec spark-master /bin/bash '
    f'spark-submit {PACKAGES} {JARS} /opt/bitnami/spark/myjars/constraints/check_customer.py',
    dag=dag,
)

check_table_trade = BashOperator(
    task_id='check_table_trade',
    bash_command='docker exec spark-master /bin/bash '
    f'spark-submit {PACKAGES} {JARS} /opt/bitnami/spark/myjars/constraints/check_trade.py',
    dag=dag,
)

check_table_stocks = BashOperator(
    task_id='check_table_stocks',
    bash_command='docker exec spark-master /bin/bash '
    f'spark-submit {PACKAGES} {JARS} /opt/bitnami/spark/myjars/constraints/check_stock.py'
    ' stock_AAPL stock_AMZN stock_GOOGL stock_META stock_MSFT',
    dag=dag,
)

get_all_table_profiles = BashOperator(
    task_id='get_all_table_profiles',
    bash_command='docker exec spark-master /bin/bash '
    f'spark-submit {PACKAGES} {JARS} /opt/bitnami/spark/myjars/get_df_profiles.py',
    dag=dag,
)


transfer_db_to_dw = BashOperator(
    task_id='transfer_db_to_dw',
    bash_command='docker exec spark-master /bin/bash '
    f'spark-submit {PACKAGES} {JARS} /opt/bitnami/spark/myjars/transfer_db_to_big.py all',
    dag=dag,
)

check_table_budget >> check_table_customer >> check_table_trade >> check_table_stocks \
    >> get_all_table_profiles >> transfer_db_to_dw
