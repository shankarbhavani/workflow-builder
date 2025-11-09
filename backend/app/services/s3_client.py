"""
S3 client for uploading files and generating presigned URLs
"""
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class S3Client:
    """Client for AWS S3 operations"""

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region: str = "us-east-1"
    ):
        """
        Initialize S3 client

        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region: AWS region
        """
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region
        )
        self.region = region

    def upload_file(
        self,
        file_data: bytes,
        bucket_name: str,
        s3_key: str
    ) -> bool:
        """
        Upload file to S3

        Args:
            file_data: File data as bytes
            bucket_name: S3 bucket name
            s3_key: S3 object key (path)

        Returns:
            True if upload successful, False otherwise
        """
        try:
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file_data
            )
            logger.info(f"Successfully uploaded file to s3://{bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"AWS ClientError uploading file to S3: {str(e)}")
            return False
        except BotoCoreError as e:
            logger.error(f"AWS BotoCoreError uploading file to S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading file to S3: {str(e)}")
            return False

    def generate_presigned_url(
        self,
        bucket_name: str,
        s3_key: str,
        expiration_hours: int = 24
    ) -> Optional[str]:
        """
        Generate presigned URL for S3 object

        Args:
            bucket_name: S3 bucket name
            s3_key: S3 object key
            expiration_hours: URL expiration time in hours

        Returns:
            Presigned URL string or None if failed
        """
        try:
            expiration_seconds = expiration_hours * 3600
            presigned_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": s3_key},
                ExpiresIn=expiration_seconds
            )
            logger.info(f"Generated presigned URL for s3://{bucket_name}/{s3_key} (expires in {expiration_hours}h)")
            return presigned_url
        except ClientError as e:
            logger.error(f"AWS ClientError generating presigned URL: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None

    def upload_and_get_presigned_url(
        self,
        file_data: bytes,
        filename: str,
        bucket_name: str,
        folder_path: str = "",
        expiration_hours: int = 24
    ) -> Optional[str]:
        """
        Upload file to S3 and generate presigned URL

        Args:
            file_data: File data as bytes
            filename: Original filename
            bucket_name: S3 bucket name
            folder_path: S3 folder path (e.g., "bhavani")
            expiration_hours: URL expiration time in hours

        Returns:
            Presigned URL or None if failed
        """
        # Generate S3 key with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if folder_path:
            s3_key = f"{folder_path}/{timestamp}_{filename}"
        else:
            s3_key = f"{timestamp}_{filename}"

        # Upload file
        if not self.upload_file(file_data, bucket_name, s3_key):
            return None

        # Generate presigned URL
        return self.generate_presigned_url(bucket_name, s3_key, expiration_hours)

    def check_bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if S3 bucket exists and is accessible

        Args:
            bucket_name: S3 bucket name

        Returns:
            True if bucket exists and is accessible, False otherwise
        """
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"Bucket {bucket_name} exists and is accessible")
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                logger.error(f"Bucket {bucket_name} does not exist")
            elif error_code == "403":
                logger.error(f"Access denied to bucket {bucket_name}")
            else:
                logger.error(f"Error checking bucket {bucket_name}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking bucket {bucket_name}: {str(e)}")
            return False
