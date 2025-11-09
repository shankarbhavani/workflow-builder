"""
Gmail IMAP client for reading emails and downloading attachments
"""
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GmailClient:
    """Client for Gmail IMAP operations"""

    def __init__(self, email_address: str, app_password: str):
        """
        Initialize Gmail client with app password authentication

        Args:
            email_address: Gmail email address
            app_password: Gmail app password (not regular password)
        """
        self.email_address = email_address
        self.app_password = app_password
        self.imap = None

    def connect(self) -> bool:
        """
        Connect to Gmail IMAP server

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            self.imap.login(self.email_address, self.app_password)
            logger.info(f"Successfully connected to Gmail for {self.email_address}")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"Gmail IMAP authentication failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Gmail: {str(e)}")
            return False

    def disconnect(self):
        """Close IMAP connection"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except Exception as e:
                logger.warning(f"Error disconnecting from Gmail: {str(e)}")

    def search_emails(
        self,
        time_range_start: Optional[datetime] = None,
        time_range_end: Optional[datetime] = None,
        only_unread: bool = True
    ) -> List[bytes]:
        """
        Search for emails within time range

        Args:
            time_range_start: Start datetime for email search
            time_range_end: End datetime for email search
            only_unread: If True, only search unread emails

        Returns:
            List of email IDs
        """
        if not self.imap:
            logger.error("Not connected to Gmail")
            return []

        try:
            # Select inbox
            self.imap.select("INBOX")

            # Build search criteria
            search_criteria = []

            if only_unread:
                search_criteria.append("UNSEEN")

            if time_range_start:
                date_str = time_range_start.strftime("%d-%b-%Y")
                search_criteria.append(f'SINCE "{date_str}"')

            if time_range_end:
                date_str = time_range_end.strftime("%d-%b-%Y")
                search_criteria.append(f'BEFORE "{date_str}"')

            # If no criteria, search all emails
            if not search_criteria:
                search_criteria.append("ALL")

            # Execute search
            search_string = " ".join(search_criteria)
            status, messages = self.imap.search(None, search_string)

            if status != "OK":
                logger.error(f"Email search failed with status: {status}")
                return []

            # Get list of email IDs
            email_ids = messages[0].split()
            logger.info(f"Found {len(email_ids)} emails matching criteria")
            return email_ids

        except Exception as e:
            logger.error(f"Error searching emails: {str(e)}")
            return []

    def download_pdf_attachments(
        self,
        email_id: bytes
    ) -> List[Tuple[str, bytes]]:
        """
        Download PDF attachments from an email

        Args:
            email_id: Email ID to process

        Returns:
            List of tuples (filename, file_data) for PDF attachments
        """
        attachments = []

        try:
            # Fetch email
            status, msg_data = self.imap.fetch(email_id, "(RFC822)")
            if status != "OK":
                logger.error(f"Failed to fetch email {email_id}")
                return attachments

            # Parse email
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)

            # Iterate through email parts
            for part in email_message.walk():
                # Check if part is an attachment
                if part.get_content_maintype() == "multipart":
                    continue
                if part.get("Content-Disposition") is None:
                    continue

                # Get filename
                filename = part.get_filename()
                if not filename:
                    continue

                # Decode filename if needed
                decoded = decode_header(filename)
                if decoded[0][1]:
                    filename = decoded[0][0].decode(decoded[0][1])
                else:
                    filename = decoded[0][0] if isinstance(decoded[0][0], str) else decoded[0][0].decode()

                # Check if it's a PDF
                if not filename.lower().endswith(".pdf"):
                    logger.debug(f"Skipping non-PDF attachment: {filename}")
                    continue

                # Get attachment data
                file_data = part.get_payload(decode=True)
                if file_data:
                    attachments.append((filename, file_data))
                    logger.info(f"Downloaded PDF attachment: {filename}")

        except Exception as e:
            logger.error(f"Error downloading attachments from email {email_id}: {str(e)}")

        return attachments

    def mark_as_read(self, email_id: bytes) -> bool:
        """
        Mark email as read

        Args:
            email_id: Email ID to mark as read

        Returns:
            True if successful, False otherwise
        """
        try:
            self.imap.store(email_id, "+FLAGS", "\\Seen")
            logger.debug(f"Marked email {email_id} as read")
            return True
        except Exception as e:
            logger.error(f"Error marking email {email_id} as read: {str(e)}")
            return False

    def process_emails_with_pdf_attachments(
        self,
        time_range_start: Optional[datetime] = None,
        time_range_end: Optional[datetime] = None
    ) -> List[Dict[str, any]]:
        """
        Process emails and extract PDF attachments

        Args:
            time_range_start: Start datetime for email search
            time_range_end: End datetime for email search

        Returns:
            List of dicts with email_id, attachments (list of filename, data tuples)
        """
        results = []

        # Connect to Gmail
        if not self.connect():
            return results

        try:
            # Search for emails
            email_ids = self.search_emails(time_range_start, time_range_end, only_unread=True)

            # Process each email one by one
            for email_id in email_ids:
                # Download PDF attachments
                attachments = self.download_pdf_attachments(email_id)

                # Only include emails with PDF attachments
                if attachments:
                    results.append({
                        "email_id": email_id.decode(),
                        "attachments": attachments
                    })

                    # Mark as read
                    self.mark_as_read(email_id)
                else:
                    logger.debug(f"Email {email_id} has no PDF attachments, skipping")

        finally:
            # Always disconnect
            self.disconnect()

        logger.info(f"Processed {len(results)} emails with PDF attachments")
        return results
