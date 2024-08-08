import json
import boto3
import subprocess

def lambda_handler(event, context):
    notebook_name = event['notebook_name']
    aws_region = event['aws_region']
    s3_bucket = event['s3_bucket']
    s3_key_prefix = event['s3_key_prefix']
    output_s3_bucket = event['output_s3_bucket']
    output_s3_key_prefix = event['output_s3_key_prefix']

    sagemaker_client = boto3.client('sagemaker', region_name=aws_region)

    # Start the notebook instance
    sagemaker_client.start_notebook_instance(NotebookInstanceName=notebook_name)
    
    # Wait for the instance to be in service
    waiter = sagemaker_client.get_waiter('notebook_instance_in_service')
    waiter.wait(NotebookInstanceName=notebook_name)

    # Run the notebook
    run_notebook(notebook_name, s3_bucket, s3_key_prefix, output_s3_bucket, output_s3_key_prefix)
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Notebook {notebook_name} started and running')
    }

def run_notebook(notebook_instance_name, s3_bucket, s3_key_prefix, output_s3_bucket, output_s3_key_prefix):
    # Download the notebook from S3
    local_path = f"/home/ec2-user/SageMaker/{s3_key_prefix}"
    s3_client = boto3.client('s3', region_name='us-east-1')
    s3_client.download_file(s3_bucket, f"{s3_key_prefix}/{notebook_instance_name}.ipynb", local_path)

    # Use papermill to run the notebook
    executed_notebook_path = f"{local_path}_executed.ipynb"
    subprocess.run([
        'papermill',
        local_path,
        executed_notebook_path
    ], check=True)

    # Upload the executed notebook back to S3
    s3_client.upload_file(executed_notebook_path, output_s3_bucket, f"{output_s3_key_prefix}/{notebook_instance_name}_executed.ipynb")
