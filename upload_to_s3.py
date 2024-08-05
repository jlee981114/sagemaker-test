import boto3
import os
import glob

def upload_notebooks():
    s3_bucket = os.environ.get('S3_BUCKET')  # Get S3 bucket name from environment variables
    s3_key_prefix = os.environ.get('S3_KEY_PREFIX')  # Get S3 key prefix from environment variables

    if not s3_bucket or not s3_key_prefix:
        raise ValueError("S3_BUCKET and S3_KEY_PREFIX environment variables must be set")

    # Create S3 client
    s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION'))

    # Find all .ipynb files in the current directory
    for notebook in glob.glob('*.ipynb'):
        s3_key = f'{s3_key_prefix}/{notebook}'
        s3_client.upload_file(notebook, s3_bucket, s3_key)
        print(f'Notebook uploaded to s3://{s3_bucket}/{s3_key}')

if __name__ == "__main__":
    upload_notebooks()
