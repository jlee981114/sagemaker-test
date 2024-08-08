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
    domain_id = os.environ.get('DOMAIN_ID')
    role_arn = os.environ.get('ROLE_ARN')
    aws_region = os.environ.get('AWS_REGION')
    subnet_ids = os.environ.get('SUBNET_IDS').split(',')  # Expecting comma-separated subnet IDs
    vpc_id = os.environ.get('VPC_ID')

    if not domain_name or not domain_id or not role_arn or not aws_region or not subnet_ids or not vpc_id:
        raise ValueError("DOMAIN_NAME, DOMAIN_ID, ROLE_ARN, AWS_REGION, SUBNET_IDS, and VPC_ID environment variables must be set")

    sagemaker_client = boto3.client('sagemaker', region_name=aws_region)

    try:
        response = sagemaker_client.describe_domain(DomainId=domain_id)
        print(f'SageMaker Studio domain {domain_id} exists.')
    except sagemaker_client.exceptions.ResourceNotFound:
        print(f'Creating SageMaker Studio domain {domain_id}.')
        sagemaker_client.create_domain(
            DomainName=domain_name,
            DomainId=domain_id,
            AuthMode='IAM',
            DefaultUserSettings={
                'ExecutionRole': role_arn
            },
            SubnetIds=subnet_ids,
            VpcId=vpc_id
        )
        print(f'SageMaker Studio domain {domain_name} ({domain_id}) created.')

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

if __name__ == "__main__":
    upload_notebooks()
    create_sagemaker_studio_domain()
    create_sagemaker_studio_user()
