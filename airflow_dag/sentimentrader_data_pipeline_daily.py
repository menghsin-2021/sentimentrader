from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow.providers.ssh.hooks.ssh import SSHHook
from dotenv import load_dotenv

SSH_PATH = os.getenv('SSH_PATH')
EMAIL = os.getenv('EMAIL')
OWNER = os.getenv('OWNER')
EC2_01_IP = os.getenv('EC2_01_IP')
EC2_02_IP = os.getenv('EC2_02_IP')
EC2_USER = os.getenv('EC2_USER')
PEM = os.getenv('PEM')
SSH_PORT = os.getenv('SSH_PORT')

import os
os.chdir(SSH_PATH)

default_args = {
    'owner': OWNER,
    'depends_on_past': False,
    'start_date': datetime(2021, 11, 11),
    'email': [EMAIL],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG('sentimentrader', default_args=default_args, schedule_interval='30 14 * * *')

# ec2
data_pipeline = SSHHook(
    remote_host=EC2_01_IP,
    username=EC2_USER,
    key_file=PEM,
    port=SSH_PORT
)

# ec2
data_pipeline_selenium = SSHHook(
    remote_host=EC2_02_IP,
    username=EC2_USER,
    key_file=PEM,
    port=SSH_PORT
)

# craw daily information
test_connection = SSHOperator(
    task_id="test_connection",
    ssh_hook=data_pipeline,
    ssh_conn_id='ssh_t4g',
    command='pwd',
    dag=dag
)

ptt_crawler = SSHOperator(
    task_id="craw_ptt",
    ssh_hook=data_pipeline,
    ssh_conn_id='ssh_t4g',
    command='source craw_ptt.sh ',
    dag=dag
)

cynes_crawler = SSHOperator(
    task_id="craw_cnyes",
    ssh_hook=data_pipeline,
    ssh_conn_id='ssh_t4g',
    command='source craw_cnyes.sh ',
    dag=dag
)

stock_price_crawler = SSHOperator(
    task_id="craw_stock_price",
    ssh_hook=data_pipeline_selenium,
    ssh_conn_id='ssh_t2',
    command='source craw_stock_price.sh ',
    dag=dag
)


# article_tag
ptt_cut_tag = SSHOperator(
    task_id="ptt_cut_tag",
    ssh_hook=data_pipeline,
    ssh_conn_id='ssh_new',
    command='source cut_tag_ptt.sh ',
    dag=dag
)
#
cnyes_cut_tag = SSHOperator(
    task_id="cnyes_cut_tag",
    ssh_hook=data_pipeline,
    ssh_conn_id='ssh_new',
    command='source cut_tag_cnyes.sh ',
    dag=dag
)
#
# word_count
word_count = SSHOperator(
    task_id="word_count",
    ssh_hook=data_pipeline,
    ssh_conn_id='ssh_new',
    command='source word_count.sh ',
    dag=dag
)
#
# material view
material_view = SSHOperator(
    task_id="create_material_view",
    ssh_hook=data_pipeline,
    ssh_conn_id='ssh_new',
    command='source create_material_view.sh ',
    dag=dag
)


# 把流程整個串起來．

test_connection >> ptt_crawler >> cynes_crawler >> ptt_cut_tag >> cnyes_cut_tag >> word_count >> material_view
test_connection >> stock_price_crawler >> ptt_cut_tag >> cnyes_cut_tag >> word_count >> material_view