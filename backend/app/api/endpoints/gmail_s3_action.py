"""
Gmail to S3 Action API endpoint
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Dict
import logging

from app.core.security import get_current_user
from app.core.config import settings
from app.schemas.gmail_s3_action import (
    GmailS3ActionRequest,
    GmailS3ActionResponse,
    AttachmentsData
)
from app.services.gmail_client import GmailClient
from app.services.s3_client import S3Client

router = APIRouter(prefix="/actions/execute", tags=["actions"])
logger = logging.getLogger(__name__)


@router.post("/gmail_download_attachments_to_s3", response_model=GmailS3ActionResponse)
async def gmail_download_attachments_to_s3(
    request: GmailS3ActionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Read emails from Gmail, download PDF attachments, upload to S3, and return presigned URLs

    **Workflow:**
    1. Connect to Gmail using IMAP with app password
    2. Search for emails within specified time range (defaults to all unread)
    3. Download only PDF attachments from matching emails
    4. Upload PDFs to S3 bucket under specified folder
    5. Generate 24-hour presigned URLs for each file
    6. Mark processed emails as read
    7. Return dictionary mapping {filename: presigned_url}

    **Parameters:**
    - gmail_email: Gmail address to read from
    - gmail_app_password: Gmail app password (not regular password!)
    - time_range_start: Optional start datetime (ISO format)
    - time_range_end: Optional end datetime (ISO format)
    - s3_folder: S3 folder path (default: "bhavani")

    **Returns:**
    - attachments: Dict mapping filename to presigned S3 URL
    - processed_emails: Number of emails processed
    - total_attachments: Number of PDF attachments downloaded
    """
    audit = []

    try:
        # Extract configuration
        config = request.configurations
        event_data = request.event_data

        audit.append({
            "step": "START",
            "action": "gmail_download_attachments_to_s3",
            "shipper_id": event_data.shipper_id,
            "agent_id": event_data.agent_id,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Parse time range if provided
        time_range_start = None
        time_range_end = None

        if config.time_range_start:
            try:
                time_range_start = datetime.fromisoformat(config.time_range_start)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid time_range_start format: {config.time_range_start}"
                )

        if config.time_range_end:
            try:
                time_range_end = datetime.fromisoformat(config.time_range_end)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid time_range_end format: {config.time_range_end}"
                )

        # Initialize Gmail client
        gmail_client = GmailClient(
            email_address=config.gmail_email,
            app_password=config.gmail_app_password
        )

        audit.append({
            "step": "GMAIL_CONNECT",
            "status": "IN_PROGRESS",
            "email": config.gmail_email
        })

        # Process emails and download PDF attachments
        email_results = gmail_client.process_emails_with_pdf_attachments(
            time_range_start=time_range_start,
            time_range_end=time_range_end
        )

        if not email_results:
            audit.append({
                "step": "GMAIL_PROCESS",
                "status": "COMPLETED",
                "message": "No emails with PDF attachments found"
            })

            return GmailS3ActionResponse(
                data={
                    "attachments": {},
                    "processed_emails": 0,
                    "total_attachments": 0,
                    "s3_bucket": settings.S3_BUCKET_NAME,
                    "s3_folder": config.s3_folder
                },
                audit=audit
            )

        audit.append({
            "step": "GMAIL_PROCESS",
            "status": "COMPLETED",
            "emails_found": len(email_results),
            "total_attachments": sum(len(email["attachments"]) for email in email_results)
        })

        # Initialize S3 client
        s3_client = S3Client(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region=settings.AWS_REGION
        )

        # Check if bucket exists
        if not s3_client.check_bucket_exists(settings.S3_BUCKET_NAME):
            raise HTTPException(
                status_code=500,
                detail=f"S3 bucket {settings.S3_BUCKET_NAME} does not exist or is not accessible"
            )

        # Upload attachments to S3 and generate presigned URLs
        attachments_dict = {}
        upload_failures = []

        for email_data in email_results:
            for filename, file_data in email_data["attachments"]:
                try:
                    presigned_url = s3_client.upload_and_get_presigned_url(
                        file_data=file_data,
                        filename=filename,
                        bucket_name=settings.S3_BUCKET_NAME,
                        folder_path=config.s3_folder,
                        expiration_hours=24
                    )

                    if presigned_url:
                        attachments_dict[filename] = presigned_url
                    else:
                        upload_failures.append(filename)
                        logger.error(f"Failed to upload {filename} to S3")

                except Exception as e:
                    upload_failures.append(filename)
                    logger.error(f"Error uploading {filename} to S3: {str(e)}")

        audit.append({
            "step": "S3_UPLOAD",
            "status": "COMPLETED",
            "successful_uploads": len(attachments_dict),
            "failed_uploads": len(upload_failures),
            "failed_files": upload_failures if upload_failures else []
        })

        # Build response
        response_data = {
            "attachments": attachments_dict,
            "processed_emails": len(email_results),
            "total_attachments": len(attachments_dict) + len(upload_failures),
            "s3_bucket": settings.S3_BUCKET_NAME,
            "s3_folder": config.s3_folder
        }

        if upload_failures:
            response_data["upload_failures"] = upload_failures

        audit.append({
            "step": "COMPLETE",
            "status": "SUCCESS",
            "timestamp": datetime.utcnow().isoformat()
        })

        return GmailS3ActionResponse(
            data=response_data,
            audit=audit
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in gmail_download_attachments_to_s3: {str(e)}", exc_info=True)
        audit.append({
            "step": "ERROR",
            "status": "FAILED",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process Gmail attachments: {str(e)}"
        )
