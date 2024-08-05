import boto3
import os

def upload_notebook():
    s3_bucket = os.environ.get('S3_BUCKET')  # Get S3 bucket name from environment variables
    s3_key = os.environ.get('S3_KEY')  # Get S3 key from environment variables

    if not s3_bucket or not s3_key:
        raise ValueError("S3_BUCKET and S3_KEY environment variables must be set")

    # Upload the notebook to S3
    s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION'))
    s3_client.upload_file('notebook.ipynb', s3_bucket, s3_key)

    print(f'Notebook uploaded to s3://{s3_bucket}/{s3_key}')

if __name__ == "__main__":
    upload_notebook()
