from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import BranchPythonOperator
from datetime import datetime, timedelta
import subprocess
import json


def run_yfinance_script():
    """
    Executes the extract_yfinance.py script and returns the result.
    The script is expected to output a JSON string with a 'success' key.
    """
    result = subprocess.run(
        ['python', 'extract_yfinance.py'], capture_output=True, text=True)
    output = result.stdout.strip()
    return json.loads(output).get('success', False)


def perform_data_validation():
    """
    Perform data validation checks here.
    Replace this logic with actual data validation.
    """
    print("Performing data validation...")
    return True


def save_to_database():
    """
    Save data to the database.
    Replace this logic with actual database operations.
    """
    print("Saving data to the database...")
    return True


def decide_next_step(**kwargs):
    """
    Decide the next step based on the previous task's result.
    """
    task_instance = kwargs['ti']
    success = task_instance.xcom_pull(task_ids='run_yfinance_script')
    return 'validate_data' if success else 'end_process'


def end_process():
    """
    Task to end the DAG if the previous step was not successful.
    """
    print("No valid data to process. Ending the DAG.")


# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Define the DAG
dag = DAG(
    'yfinance_etl',
    default_args=default_args,
    description='ETL process for Yahoo Finance data',
    schedule_interval='*/1 * * * *',  # Every 1 minute
    start_date=datetime(2024, 12, 29),
    catchup=False,
)

# Define tasks
run_yfinance_task = PythonOperator(
    task_id='run_yfinance_script',
    python_callable=run_yfinance_script,
    dag=dag,
)

decide_next_step_task = BranchPythonOperator(
    task_id='decide_next_step',
    python_callable=decide_next_step,
    provide_context=True,
    dag=dag,
)

validate_data_task = PythonOperator(
    task_id='validate_data',
    python_callable=perform_data_validation,
    dag=dag,
)

save_to_db_task = PythonOperator(
    task_id='save_to_database',
    python_callable=save_to_database,
    dag=dag,
)

end_process_task = DummyOperator(
    task_id='end_process',
    dag=dag,
)

# Define task dependencies
run_yfinance_task >> decide_next_step_task

decide_next_step_task >> validate_data_task >> save_to_db_task

decide_next_step_task >> end_process_task
