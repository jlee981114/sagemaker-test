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

if __name__ == "__main__":
    upload_notebooks()
