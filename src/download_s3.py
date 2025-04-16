import os
import sys
import logging
import boto3
import botocore.exceptions
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_env_var(var_name):
    value = os.getenv(var_name)
    if not value:
        logging.error(f"Environment variable '{var_name}' is not set.")
        sys.exit(1)
    return value

def download_file_from_s3(s3_client, bucket, key, destination=None):
    if not destination:
        destination = os.path.basename(key)
    try:
        s3_client.download_file(bucket, key, destination)
        logging.info(f"Successfully downloaded '{key}' to '{destination}'.")
    except botocore.exceptions.ClientError as e:
        logging.error(f"Failed to download '{key}' from bucket '{bucket}': {e}")
        raise

def shutdown_system():
    logging.error("Shutting down the system due to critical failure.")
    subprocess.call(['sudo', 'shutdown', '-h', 'now'])

def download_db(state=None):
    aws_access_key = get_env_var('AWS_A_Key')
    aws_secret_key = get_env_var('AWS_S_Key')
    aws_region = get_env_var('AWS_Region')

    bucket_name = get_env_var('BUCKET_NAME')
    food_nutrition_file_key = get_env_var('FOOD_NUTRITION_FILE_KEY')
    recipe_file_key = get_env_var('RECIPE_FILE_KEY')

    try:
        session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        s3_client = session.client('s3')

        if state is None:
            download_file_from_s3(s3_client, bucket_name, food_nutrition_file_key)
            download_file_from_s3(s3_client, bucket_name, recipe_file_key)
        elif state == 1:
            download_file_from_s3(s3_client, bucket_name, food_nutrition_file_key)
        elif state == 2:
            download_file_from_s3(s3_client, bucket_name, recipe_file_key)
        else:
            logging.warning(f"Invalid state '{state}' provided. No files will be downloaded.")

    except Exception as e:
        logging.exception("An unexpected error occurred during file download.")
        shutdown_system()
        sys.exit(1)

if __name__ == "__main__":
    pass
