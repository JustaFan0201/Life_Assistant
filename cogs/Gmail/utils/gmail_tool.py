import os
import aioimaplib
import asyncio
from aiosmtplib import SMTP
from email.message import EmailMessage
from email import message_from_bytes
import email
from email.header import decode_header

class EmailTools:
    def __init__(self):
        self.host = "smtp.gmail.com"
        self.imap_host = "imap.gmail.com"
        self.port = 465
        self.user = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASSWORD")

    async def send_mail(self, data):
        if not data.get('to'):
            return False, '收件人gmail 不得為空'
            
        try:
            msg = EmailMessage()
            msg["From"] = self.user
            msg["To"] = data['to']
            msg["Subject"] = data['subject']
            msg.set_content(data['content'])
        except Exception as e:
            return False, f'信件格式轉換失敗: {e}'

        try:
            async with SMTP(hostname=self.host, port=self.port, use_tls=True) as smtp:
                await smtp.login(self.user, self.password)
                await smtp.send_message(msg)

                return True, f"已發送email至{data['to']}"

        except ValueError as e:
            print(f"SMTP Error: {e}")
            return False, 'msg發送失敗 請通知管理員'

    async def get_unread_emails(self, last_id):
        imap_client = None
        results = []
        try:
            imap_client = aioimaplib.IMAP4_SSL(self.imap_host)

            timeout = 15
            while imap_client.protocol.state == 'STARTED' and timeout > 0:
                await asyncio.sleep(0.5)
                timeout -= 0.5
            
            await asyncio.sleep(1)
            
            await imap_client.login(self.user, self.password)
            await imap_client.select("INBOX")

            status, messages = await imap_client.search("ALL")
            if status != "OK" or not messages[0]:
                return []

            all_ids = [m.decode() for m in messages[0].split()]
            
            if last_id:
                new_ids = [m_id for m_id in all_ids if int(m_id) > int(last_id)]
            else:
                new_ids = [all_ids[-1]] if all_ids else []

            for m_id in new_ids:
                res, data = await imap_client.fetch(m_id, "(RFC822)")
                if res == "OK":
                    email_data = self._parse_latest_mail(data[1], m_id)
                    results.append(email_data)
            
            return results

        except Exception as e:
            print(f"[EmailTools] 抓取信件失敗: {e}")
            return []
        finally:
            if imap_client:
                try: await imap_client.logout()
                except: pass

    def safe_decode(self, msg, header_name):
        header_value = msg.get(header_name, "")
        if not header_value:
            return "無"
        parts = decode_header(header_value)
        decoded_parts = []
        for content, encoding in parts:
            if isinstance(content, bytes):
                decoded_parts.append(content.decode(encoding or "utf-8", errors="replace"))
            else:
                decoded_parts.append(str(content))
        return "".join(decoded_parts)

    def _get_body(self, msg):
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="replace")
                    break
        else:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")
        
        body = body.strip()
        return (body[:200] + "...") if len(body) > 200 else body

    def _parse_latest_mail(self, raw_email, msg_id):
        msg = message_from_bytes(raw_email)
        return {
            "id": msg_id,
            "from": self.safe_decode(msg, "From"),
            "subject": self.safe_decode(msg, "Subject"),
            "body": self._get_body(msg),
            "date": msg.get("Date"),
            "raw": msg
        }