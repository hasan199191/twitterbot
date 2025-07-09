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
    
    def get_latest_twitter_code(self):
        """Gmail'de konu başlığı 'X doğrulama kodun <kod>' olan en son mailden kodu döndürür."""
        try:
            logger.info("Connecting to Gmail to get X doğrulama kodu")
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email_address, self.password)
            mail.select("inbox")
            # Son 20 maili kontrol et
            status, data = mail.search(None, 'ALL')
            if status != "OK":
                logger.error("Gmail arama başarısız!")
                mail.close()
                mail.logout()
                return None
            email_ids = data[0].split()
            for eid in reversed(email_ids[-20:]):
                status, email_data = mail.fetch(eid, "(RFC822)")
                if status != "OK":
                    continue
                raw_email = email_data[0][1]
                msg = email.message_from_bytes(raw_email)
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                logger.info(f"Email subject: {subject}")
                match = re.match(r"X doğrulama kodun (\w+)", subject)
                if match:
                    code = match.group(1)
                    logger.info(f"Konu başlığından doğrulama kodu bulundu: {code}")
                    mail.store(eid, "+FLAGS", "\\Seen")
                    mail.close()
                    mail.logout()
                    return code
            mail.close()
            mail.logout()
            logger.warning("Uygun X doğrulama kodu başlıklı mail bulunamadı!")
            return None
        except Exception as e:
            logger.error(f"Gmail'den doğrulama kodu alınırken hata: {str(e)}")
            return None
            return None