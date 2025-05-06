from dotenv import load_dotenv
import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

load_dotenv(dotenv_path=".env.local")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

def get_all_files(user_id: str) -> list:
    """
    List all files in the specified S3 bucket for a given user.
    Uses pagination to handle large numbers of objects and properly formats the user prefix.
    """
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )

        paginator = s3.get_paginator('list_objects_v2')
        
        user_prefix = f"sessions/{user_id}/"
        
        page_iterator = paginator.paginate(
            Bucket=AWS_BUCKET_NAME,
            Prefix=user_prefix
        )

        file_list = []
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Key'].endswith('.mp4') or obj['Key'].endswith('.ogg'):
                        file_list.append(obj['Key'])
        
        return file_list

    except (NoCredentialsError, PartialCredentialsError) as e:
        raise Exception(f"Credentials error: {e}")
    except Exception as e:
        raise Exception(f"Error listing files: {e}")

def get_file_url(file_key: str, expiration: int = None) -> str:
    try:
        if not file_key or not isinstance(file_key, str):
            raise ValueError("Invalid file key provided")
            
        if not file_key.startswith('sessions/'):
            raise ValueError("File key must be in the sessions directory")

        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )

        default_expiration = int(os.getenv("S3_URL_EXPIRATION", 3600))
        url_expiration = expiration if expiration is not None else default_expiration
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': AWS_BUCKET_NAME,
                'Key': file_key
            },
            ExpiresIn=url_expiration,
            HttpMethod='GET'
        )

        return url

    except (NoCredentialsError, PartialCredentialsError) as e:
        raise Exception(f"AWS credential error: {str(e)}") from e
    except ValueError as ve:
        raise ve
    except Exception as e:
        raise Exception(f"Failed to generate URL: {str(e)}") from e

if __name__ == "__main__":
    user_id = "user-8983"
    try:
        files = get_all_files(user_id)
        print(f"Files for user {user_id}: {files}")
        for file in files:
            url = get_file_url(file)
            print(f"File URL: {url}")
    except Exception as e:
        print(f"Error: {e}")