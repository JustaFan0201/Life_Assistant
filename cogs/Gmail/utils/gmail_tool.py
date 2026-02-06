import os
import aioimaplib
import asyncio
from aiosmtplib import SMTP
from email.message import EmailMessage
from email import message_from_bytes
import email
import re
from email.header import decode_header
from email.utils import parseaddr

class EmailTools:
    def __init__(self, email_user=None, email_password=None):
        self.host = "smtp.gmail.com"
        self.imap_host = "imap.gmail.com"
        self.port = 465
        
        self.user = email_user or os.getenv("EMAIL_USER")
        self.password = email_password or os.getenv("EMAIL_PASSWORD")
    
    def _extract_pure_email(self, text):
        if not text: return ""
        _, addr = parseaddr(text)
        return addr.strip()

    async def send_mail(self, data):
        if not self.user or not self.password:
            return False, '尚未設置寄件者帳號或密碼'

        raw_to = data.get('to', '')
        pure_to = self._extract_pure_email(raw_to)
        
        if not pure_to:
            return False, '收件人地址解析失敗'
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, pure_to) is None:
            return False, f'Email 格式不符 (解析後為: {pure_to})'

        try:
            msg = EmailMessage()
            msg["From"] = self.user
            msg["To"] = pure_to
            msg["Subject"] = data.get('subject') or "(無主旨)"
            msg.set_content(data.get('content') or "")
            
            async with SMTP(hostname=self.host, port=self.port, use_tls=True, timeout=10) as smtp:
                await smtp.login(self.user, self.password)
                await smtp.send_message(msg)
                return True, f"已發送 email 至 {pure_to}"
                
        except asyncio.TimeoutError:
            return False, '連線超時，Gmail 伺服器無回應'
        except Exception as e:
            return False, f'發送失敗: {str(e)}'

    async def get_unread_emails(self, last_id):
        if not self.user or not self.password:
            print("[EmailTools] 錯誤: 未提供帳號密碼，跳過檢查")
            return []

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
                try:
                    new_ids = [m_id for m_id in all_ids if int(m_id) > int(last_id)]
                except ValueError:
                    new_ids = [all_ids[-1]] if all_ids else []
            else:
                new_ids = [all_ids[-1]] if all_ids else []

            for m_id in new_ids:
                res, data = await imap_client.fetch(m_id, "(RFC822)")
                if res == "OK":
                    email_data = self._parse_latest_mail(data[1], m_id)
                    results.append(email_data)
            
            return results

        except Exception as e:
            print(f"[EmailTools] 使用者 {self.user} 抓取失敗: {e}")
            return []
        finally:
            if imap_client:
                try: 
                    await imap_client.logout()
                except: 
                    pass

    def safe_decode(self, msg, header_name):
        header_value = msg.get(header_name, "")
        if not header_value:
            return "無"
        parts = decode_header(header_value)
        decoded_parts = []
        for content, encoding in parts:
            if isinstance(content, bytes):
                try:
                    decoded_parts.append(content.decode(encoding or "utf-8", errors="replace"))
                except:
                    decoded_parts.append(content.decode("latin1", errors="replace"))
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