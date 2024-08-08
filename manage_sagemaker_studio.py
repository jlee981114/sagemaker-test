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

def create_sagemaker_studio_domain():
    domain_name = os.environ.get('DOMAIN_NAME')
    role_arn = os.environ.get('ROLE_ARN')
    aws_region = os.environ.get('AWS_REGION')

    if not domain_name or not role_arn or not aws_region:
        raise ValueError("DOMAIN_NAME, ROLE_ARN, and AWS_REGION environment variables must be set")

    sagemaker_client = boto3.client('sagemaker', region_name=aws_region)

    try:
        response = sagemaker_client.describe_domain(DomainName=domain_name)
        print(f'SageMaker Studio domain {domain_name} exists.')
    except sagemaker_client.exceptions.ResourceNotFound:
        print(f'Creating SageMaker Studio domain {domain_name}.')
        sagemaker_client.create_domain(
            DomainName=domain_name,
            AuthMode='IAM',
            DefaultUserSettings={
                'ExecutionRole': role_arn
            },
            SubnetIds=['subnet-016229a0a23943e74'],  # Replace with your Subnet ID
            VpcId='vpc-086865caa3938cd2e'  # Replace with your VPC ID
        )
        print(f'SageMaker Studio domain {domain_name} created.')

def create_sagemaker_studio_user():
    domain_name = os.environ.get('DOMAIN_NAME')
    user_profile_name = os.environ.get('USER_PROFILE_NAME')
    aws_region = os.environ.get('AWS_REGION')

    if not domain_name or not user_profile_name or not aws_region:
        raise ValueError("DOMAIN_NAME, USER_PROFILE_NAME, and AWS_REGION environment variables must be set")

    sagemaker_client = boto3.client('sagemaker', region_name=aws_region)

    try:
        response = sagemaker_client.describe_user_profile(DomainId=domain_name, UserProfileName=user_profile_name)
        print(f'SageMaker Studio user profile {user_profile_name} exists.')
    except sagemaker_client.exceptions.ResourceNotFound:
        print(f'Creating SageMaker Studio user profile {user_profile_name}.')
        sagemaker_client.create_user_profile(
            DomainId=domain_name,
            UserProfileName=user_profile_name,
            UserSettings={}
        )
        print(f'SageMaker Studio user profile {user_profile_name} created.')

if __name__ == "__main__":
    upload_notebooks()
    create_sagemaker_studio_domain()
    create_sagemaker_studio_user()
