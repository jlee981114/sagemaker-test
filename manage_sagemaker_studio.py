import boto3
import os
import glob

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

def create_sagemaker_studio_user():
    domain_id = os.environ.get('DOMAIN_ID')
    user_profile_name = os.environ.get('USER_PROFILE_NAME')
    aws_region = os.environ.get('AWS_REGION')

    if not domain_id or not user_profile_name or not aws_region:
        raise ValueError("DOMAIN_ID, USER_PROFILE_NAME, and AWS_REGION environment variables must be set")

    sagemaker_client = boto3.client('sagemaker', region_name=aws_region)

    try:
        response = sagemaker_client.describe_user_profile(DomainId=domain_id, UserProfileName=user_profile_name)
        print(f'SageMaker Studio user profile {user_profile_name} exists.')
    except sagemaker_client.exceptions.ResourceNotFound:
        print(f'Creating SageMaker Studio user profile {user_profile_name}.')
        sagemaker_client.create_user_profile(
            DomainId=domain_id,
            UserProfileName=user_profile_name,
            UserSettings={}
        )
        print(f'SageMaker Studio user profile {user_profile_name} created.')

def create_and_start_notebook_jobs():
    s3_bucket = os.environ.get('S3_BUCKET')
    s3_key_prefix = os.environ.get('S3_KEY_PREFIX')
    domain_id = os.environ.get('DOMAIN_ID')
    user_profile_name = os.environ.get('USER_PROFILE_NAME')
    instance_types = ['ml.m5.large','ml.g5.xlarge']
    image_arns = ['arn:aws:sagemaker:us-east-1:081325390199:image/sagemaker-data-science-310-v1', 'arn:aws:sagemaker:us-east-1:081325390199:image/tensorflow-2.6-cpu-py38-ubuntu20.04-v1', 'arn:aws:sagemaker:us-east-1:081325390199:image/tensorflow-2.6-gpu-py38-cu112-ubuntu20.04-v1']
    lifecycle_config_arn = os.environ.get('LIFECYCLE_CONFIG_ARN') 

    if not s3_bucket or not s3_key_prefix or not domain_id or not user_profile_name:
        raise ValueError("S3_BUCKET, S3_KEY_PREFIX, DOMAIN_ID, and USER_PROFILE_NAME environment variables must be set")

    sagemaker_client = boto3.client('sagemaker', region_name=os.environ.get('AWS_REGION'))

    notebooks = glob.glob('*.ipynb')
    for notebook in notebooks:
        if "model-training" in notebook:
            s3_key = f'{s3_key_prefix}/{notebook}'
            notebook_job_name = f'{notebook.replace(".ipynb", "")}-job'

            response = sagemaker_client.create_presigned_notebook_instance_lifecycle_config(
                NotebookInstanceLifecycleConfigName=notebook_job_name,
                OnCreate=[{
                    'Content': open(notebook, 'r').read()
                }],
                OnStart=[]
            )

            response = sagemaker_client.start_notebook_instance(
                NotebookInstanceName=notebook_job_name,
                InstanceType=instance_types[0],
                RoleArn=lifecycle_config_arn,
                DirectInternetAccess='Enabled',
                VolumeSizeInGB=5,
                SubnetId='subnet-0123456789abcdefg',
                SecurityGroupIds=['sg-0123456789abcdefg'],
                NotebookInstanceLifecycleConfigName=notebook_job_name,
                DomainId=domain_id,
                UserProfileName=user_profile_name,
                NotebookInstanceImageArn=image_arns[1]
            )

            print(f'Notebook job {notebook_job_name} started for notebook {notebook}.')
        if "monitoring" in notebook:
            s3_key = f'{s3_key_prefix}/{notebook}'
            notebook_job_name = f'{notebook.replace(".ipynb", "")}-job'

            response = sagemaker_client.create_presigned_notebook_instance_lifecycle_config(
                NotebookInstanceLifecycleConfigName=notebook_job_name,
                OnCreate=[{
                    'Content': open(notebook, 'r').read()
                }],
                OnStart=[]
            )

            response = sagemaker_client.start_notebook_instance(
                NotebookInstanceName=notebook_job_name,
                InstanceType=instance_types[0],
                RoleArn=lifecycle_config_arn,
                DirectInternetAccess='Enabled',
                VolumeSizeInGB=5,
                SubnetId='subnet-0123456789abcdefg',
                SecurityGroupIds=['sg-0123456789abcdefg'],
                NotebookInstanceLifecycleConfigName=notebook_job_name,
                DomainId=domain_id,
                UserProfileName=user_profile_name,
                NotebookInstanceImageArn=image_arns[0]
            )

            print(f'Notebook job {notebook_job_name} started for notebook {notebook}.')
        else:
            s3_key = f'{s3_key_prefix}/{notebook}'
            notebook_job_name = f'{notebook.replace(".ipynb", "")}-job'

            response = sagemaker_client.create_presigned_notebook_instance_lifecycle_config(
                NotebookInstanceLifecycleConfigName=notebook_job_name,
                OnCreate=[{
                    'Content': open(notebook, 'r').read()
                }],
                OnStart=[]
            )

            response = sagemaker_client.start_notebook_instance(
                NotebookInstanceName=notebook_job_name,
                InstanceType=instance_types[1],
                RoleArn=lifecycle_config_arn,
                DirectInternetAccess='Enabled',
                VolumeSizeInGB=5,
                SubnetId='subnet-0123456789abcdefg',
                SecurityGroupIds=['sg-0123456789abcdefg'],
                NotebookInstanceLifecycleConfigName=notebook_job_name,
                DomainId=domain_id,
                UserProfileName=user_profile_name,
                NotebookInstanceImageArn=image_arns[2]
            )

            print(f'Notebook job {notebook_job_name} started for notebook {notebook}.')

if __name__ == "__main__":
    upload_notebooks()
    create_sagemaker_studio_user()
    # create_and_start_notebook_jobs()


