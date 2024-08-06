import boto3
import os
import glob
import base64
import time
import botocore.exceptions
from sagemaker import Session

def upload_notebooks():
    s3_bucket = os.environ.get('S3_BUCKET')
    s3_key_prefix = os.environ.get('S3_KEY_PREFIX')

    if not s3_bucket or not s3_key_prefix:
        raise ValueError("S3_BUCKET and S3_KEY_PREFIX environment variables must be set")

    s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION'))

    notebooks = glob.glob('*.ipynb')
    if not notebooks:
        raise ValueError("No notebooks found in the repository")

    for notebook in notebooks:
        s3_key = f'{s3_key_prefix}/{notebook}'
        s3_client.upload_file(notebook, s3_bucket, s3_key)
        print(f'Notebook uploaded to s3://{s3_bucket}/{s3_key}')

def create_lifecycle_config():
    lifecycle_config_name = os.environ.get('LIFECYCLE_CONFIG_NAME')
    s3_bucket = os.environ.get('S3_BUCKET')
    s3_key_prefix = os.environ.get('S3_KEY_PREFIX')

    if not lifecycle_config_name or not s3_bucket or not s3_key_prefix:
        raise ValueError("LIFECYCLE_CONFIG_NAME, S3_BUCKET, and S3_KEY_PREFIX environment variables must be set")

    lifecycle_config_content = f'''#!/bin/bash
set -e

# Variables
S3_BUCKET="{s3_bucket}"
S3_KEY_PREFIX="{s3_key_prefix}"
LOCAL_PATH="/home/ec2-user/SageMaker/"

# Download all notebooks from S3
aws s3 sync s3://$S3_BUCKET/$S3_KEY_PREFIX $LOCAL_PATH
'''

    # Encode the lifecycle configuration content as base64
    lifecycle_config_content_base64 = base64.b64encode(lifecycle_config_content.encode('utf-8')).decode('utf-8')

    sagemaker_client = boto3.client('sagemaker', region_name=os.environ.get('AWS_REGION'))

    try:
        sagemaker_client.create_notebook_instance_lifecycle_config(
            NotebookInstanceLifecycleConfigName=lifecycle_config_name,
            OnStart=[{'Content': lifecycle_config_content_base64}]
        )
        print(f'Lifecycle configuration {lifecycle_config_name} created.')
    except sagemaker_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException' and 'already exists' in e.response['Error']['Message']:
            print(f'Lifecycle configuration {lifecycle_config_name} already exists.')
        else:
            raise

def start_sagemaker_notebook_instance():
    notebook_instance_name = os.environ.get('NOTEBOOK_INSTANCE_NAME')
    instance_type = os.environ.get('INSTANCE_TYPE')
    role_arn = os.environ.get('ROLE_ARN')
    lifecycle_config_name = os.environ.get('LIFECYCLE_CONFIG_NAME')
    aws_region = os.environ.get('AWS_REGION')

    # Print environment variables for debugging
    print(f"NOTEBOOK_INSTANCE_NAME: {notebook_instance_name}")
    print(f"INSTANCE_TYPE: {instance_type}")
    print(f"ROLE_ARN: {role_arn}")
    print(f"LIFECYCLE_CONFIG_NAME: {lifecycle_config_name}")
    print(f"AWS_REGION: {aws_region}")

    if not notebook_instance_name or not instance_type or not role_arn or not lifecycle_config_name or not aws_region:
        raise ValueError("NOTEBOOK_INSTANCE_NAME, INSTANCE_TYPE, ROLE_ARN, LIFECYCLE_CONFIG_NAME, and AWS_REGION environment variables must be set")

    sagemaker_client = Session(boto_session=boto3.Session(region_name=aws_region)).sagemaker_client

    try:
        response = sagemaker_client.describe_notebook_instance(NotebookInstanceName=notebook_instance_name)
        print(f'Notebook instance {notebook_instance_name} exists with status {response["NotebookInstanceStatus"]}.')
    except sagemaker_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException' and 'RecordNotFound' in e.response['Error']['Message']:
            print(f'Creating notebook instance {notebook_instance_name}.')
            sagemaker_client.create_notebook_instance(
                NotebookInstanceName=notebook_instance_name,
                InstanceType=instance_type,
                RoleArn=role_arn,
                LifecycleConfigName=lifecycle_config_name,
                DirectInternetAccess='Enabled',
                VolumeSizeInGB=5,
                RootAccess='Enabled'
            )
            current_status = 'Pending'
        else:
            raise
    else:
        current_status = response['NotebookInstanceStatus']

    if current_status == 'Pending':
        print(f'Current status is {current_status}. Waiting for it to be in Stopped state...')
        waiter = sagemaker_client.get_waiter('notebook_instance_stopped')
        waiter.wait(NotebookInstanceName=notebook_instance_name)
        print(f'Notebook instance {notebook_instance_name} has stopped.')
    elif current_status != 'Stopped':
        print(f'Current status is {current_status}. Waiting for it to stop...')
        waiter = sagemaker_client.get_waiter('notebook_instance_stopped')
        waiter.wait(NotebookInstanceName=notebook_instance_name)
        print(f'Notebook instance {notebook_instance_name} has stopped.')

    print(f'Starting notebook instance {notebook_instance_name}.')
    sagemaker_client.start_notebook_instance(NotebookInstanceName=notebook_instance_name)

    waiter = sagemaker_client.get_waiter('notebook_instance_in_service')
    try:
        waiter.wait(NotebookInstanceName=notebook_instance_name)
        print(f'Notebook instance {notebook_instance_name} is now in service.')
    except botocore.exceptions.WaiterError as e:
        print(f'Failed to start notebook instance: {e}')
        response = sagemaker_client.describe_notebook_instance(NotebookInstanceName=notebook_instance_name)
        print(f'Current status: {response["NotebookInstanceStatus"]}')
        if "FailureReason" in response:
            print(f'Failure reason: {response["FailureReason"]}')

if __name__ == "__main__":
    upload_notebooks()
    create_lifecycle_config()
    start_sagemaker_notebook_instance()
