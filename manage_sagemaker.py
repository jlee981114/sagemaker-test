import boto3
import os
import glob
import base64

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
    image_name = os.environ.get('IMAGE_NAME')

    if not notebook_instance_name or not instance_type or not role_arn or not lifecycle_config_name or not image_name:
        raise ValueError("NOTEBOOK_INSTANCE_NAME, INSTANCE_TYPE, ROLE_ARN, LIFECYCLE_CONFIG_NAME, and IMAGE_NAME environment variables must be set")

    sagemaker_client = boto3.client('sagemaker', region_name=os.environ.get('AWS_REGION'))

    try:
        response = sagemaker_client.describe_notebook_instance(NotebookInstanceName=notebook_instance_name)
        instance_exists = True
    except sagemaker_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException' and 'RecordNotFound' in e.response['Error']['Message']:
            instance_exists = False
        else:
            raise

    if not instance_exists:
        print(f'Creating notebook instance {notebook_instance_name}.')
        sagemaker_client.create_notebook_instance(
            NotebookInstanceName=notebook_instance_name,
            InstanceType=instance_type,
            RoleArn=role_arn,
            LifecycleConfigName=lifecycle_config_name,
            DirectInternetAccess='Enabled',
            VolumeSizeInGB=5,
            RootAccess='Enabled',
            CustomImageArn=image_name
        )
    else:
        print(f'Notebook instance {notebook_instance_name} already exists. Starting it.')

    sagemaker_client.start_notebook_instance(NotebookInstanceName=notebook_instance_name)

    waiter = sagemaker_client.get_waiter('notebook_instance_in_service')
    waiter.wait(NotebookInstanceName=notebook_instance_name)
    print(f'Notebook instance {notebook_instance_name} is now in service.')

if __name__ == "__main__":
    upload_notebooks()
    create_lifecycle_config()
    start_sagemaker_notebook_instance()
