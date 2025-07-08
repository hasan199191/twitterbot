import os
import re
import imaplib
import email
import logging
from email.header import decode_header
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GmailReader:
    def __init__(self):
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.password = os.getenv("GMAIL_APP_PASSWORD")
        
        if not self.email_address or not self.password:
            raise ValueError("EMAIL_ADDRESS or GMAIL_APP_PASSWORD environment variables not set")
    
    def get_twitter_verification_code(self):
        """Get Twitter verification code from Gmail"""
        try:
            logger.info("Connecting to Gmail to get Twitter/X verification code")
            
            # Connect to Gmail
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email_address, self.password)
            mail.select("inbox")
            logger.info("Successfully connected to Gmail inbox")
            
            # First try to find emails with the exact subject pattern "Your X confirmation code is..."
            specific_subject = '(SUBJECT "Your X confirmation code is")'
            logger.info(f"Searching with very specific criteria: {specific_subject}")
            status, data = mail.search(None, specific_subject)
            
            if status == "OK" and data[0]:
                email_ids = data[0].split()
                if email_ids:
                    latest_email_id = email_ids[-1]
                    logger.info(f"Found exact match email with ID: {latest_email_id}")
                    
                    # Fetch the email
                    status, email_data = mail.fetch(latest_email_id, "(RFC822)")
                    if status == "OK":
                        raw_email = email_data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        subject = decode_header(msg["Subject"])[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()
                        
                        logger.info(f"Email subject: {subject}")
                        
                        # Extract code from the subject line (format: "Your X confirmation code is b7q3ve6g")
                        code_match = re.search(r'confirmation code is (\w+)', subject)
                        if code_match:
                            code = code_match.group(1)
                            logger.info(f"Extracted confirmation code from subject: {code}")
                            
                            # Mark email as read
                            mail.store(latest_email_id, "+FLAGS", "\\Seen")
                            mail.close()
                            mail.logout()
                            
                            return code
            
            # If we didn't find an exact match, try more general searches
            logger.info("No exact match found, trying broader search criteria")
            search_criteria = [
                '(FROM "info@x.com" SUBJECT "confirmation code")',  # Don't limit to UNSEEN
                '(SUBJECT "Your X confirmation code")'
            ]
            
            for criteria in search_criteria:
                logger.info(f"Searching with criteria: {criteria}")
                status, data = mail.search(None, criteria)
                if status == "OK" and data[0]:
                    email_ids = data[0].split()
                    if email_ids:
                        # Get the latest email
                        latest_email_id = email_ids[-1]
                        logger.info(f"Found matching email with ID: {latest_email_id}")
                        
                        # Fetch the email
                        status, email_data = mail.fetch(latest_email_id, "(RFC822)")
                        
                        if status == "OK":
                            raw_email = email_data[0][1]
                            msg = email.message_from_bytes(raw_email)
                            subject = decode_header(msg["Subject"])[0][0]
                            if isinstance(subject, bytes):
                                subject = subject.decode()
                                
                            logger.info(f"Email subject: {subject}")
                            
                            # Check if subject contains "confirmation code is"
                            if "confirmation code is" in subject:
                                code_match = re.search(r'code is (\w+)', subject)
                                if code_match:
                                    code = code_match.group(1)
                                    logger.info(f"Extracted code from subject: {code}")
                                    
                                    # Mark email as read
                                    mail.store(latest_email_id, "+FLAGS", "\\Seen")
                                    mail.close()
                                    mail.logout()
                                    
                                    return code
                            
                            # If not in subject, check body but only for specific patterns
                            for part in msg.walk():
                                if part.get_content_type() in ["text/plain", "text/html"]:
                                    try:
                                        body = part.get_payload(decode=True).decode()
                                        
                                        # Only look for very specific patterns
                                        specific_patterns = [
                                            r'confirmation code is (\w+)',
                                            r'verification code is (\w+)',
                                            r'Your X confirmation code is (\w+)'
                                        ]
                                        
                                        for pattern in specific_patterns:
                                            code_match = re.search(pattern, body)
                                            if code_match:
                                                code = code_match.group(1)
                                                logger.info(f"Extracted specific code from body: {code}")
                                                
                                                # Mark email as read
                                                mail.store(latest_email_id, "+FLAGS", "\\Seen")
                                                mail.close()
                                                mail.logout()
                                                
                                                return code
                                    except Exception as e:
                                        logger.error(f"Error processing email part: {str(e)}")
            
            logger.warning("Could not find any Twitter/X verification code in emails")
            mail.close()
            mail.logout()
            return None
                
        except Exception as e:
            logger.error(f"Error retrieving Twitter verification code: {str(e)}")
            return None