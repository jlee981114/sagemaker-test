#!/bin/bash

set -e

# Variables
S3_BUCKET="justin-automation-output"
S3_KEY_PREFIX="notebooks"
LOCAL_PATH="/home/sagemaker-user/SageMaker/Automationtest"

# Create the local directory if it doesn't exist
mkdir -p $LOCAL_PATH

# Sync notebooks from S3 to the local directory
aws s3 sync s3://$S3_BUCKET/$S3_KEY_PREFIX $LOCAL_PATH
