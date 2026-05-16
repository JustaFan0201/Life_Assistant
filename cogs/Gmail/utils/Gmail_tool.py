import os
import aioimaplib
import asyncio
from aiosmtplib import SMTP
from email.message import EmailMessage
from email import message_from_bytes
import email
import re
import html
from email.header import decode_header
from email.utils import parseaddr

class EmailTools:
    def __init__(self, email_user=None, email_password=None):
        self.host = "smtp.gmail.com"
        self.imap_host = "imap.gmail.com"
        self.port = 465
        
        self.user = email_user
        self.password = email_password
    
    def _extract_pure_email(self, text):
        if not text: return ""
        _, addr = parseaddr(text)
        return addr.strip()

    async def get_unread_emails(self, last_id):
        if not self.user or not self.password:
            print("[EmailTools] 錯誤: 未提供帳號密碼，跳過檢查")
            return [], None

        imap_client = None
        results = []
        drift_fix_id = None

        try:
            imap_client = aioimaplib.IMAP4_SSL(self.imap_host)

            timeout = 15
            while imap_client.protocol.state == 'STARTED' and timeout > 0:
                await asyncio.sleep(0.5)
                timeout -= 0.5
            
            await asyncio.sleep(1)

            login_res = await imap_client.login(self.user, self.password)

            if login_res.result != 'OK':
                raise ValueError("AUTH_FAILED")

            # await imap_client.login(self.user, self.password)
            await imap_client.select("INBOX")

            status, messages = await imap_client.search("ALL")
            if status != "OK" or not messages[0]:
                return [], None

            all_ids = [int(m.decode()) for m in messages[0].split()]
            if not all_ids:
                return [], None
            
            new_ids = []
            if last_id and str(last_id).isdigit():
                last_id_int = int(last_id)
                max_id = all_ids[-1]
                
                if last_id_int > max_id:
                    print(f"⚠️ [EmailTools] 序列號偏移 (舊:{last_id_int} > 新:{max_id})，僅發送校正訊號，不重複抓取！")
                    #  記錄需要校正的 ID，但 new_ids 保持為空，這樣就不會去 fetch 信件內容了
                    drift_fix_id = str(max_id) 
                else:
                    new_ids = [str(i) for i in all_ids if i > last_id_int]
            else:
                new_ids = [str(i) for i in all_ids[-3:]]

            for m_id in new_ids:
                res, data = await imap_client.fetch(m_id, "(RFC822)")
                if res == "OK":
                    email_data = self._parse_latest_mail(data[1], m_id)
                    results.append(email_data)
            
            return results, drift_fix_id

        except Exception as e:
            # 判斷是否為密碼錯誤
            err_msg = str(e).upper()
            if "AUTHENTICATION FAILED" in err_msg or "INVALID CREDENTIALS" in err_msg or "AUTH_FAILED" in err_msg:
                print(f"[EmailTools] 使用者 {self.user} 驗證失敗 (密碼錯誤)")
                raise ValueError("AUTH_FAILED") # 丟給 Cog 處理停用與通知
            
            print(f"⚠️ [EmailTools] 使用者 {self.user} 抓取發生其他錯誤: {e}")
            return [], None # 其他錯誤 則回傳空值，不拋出異常
        finally:
            if imap_client:
                try: 
                    await imap_client.logout()
                except Exception:
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
                except Exception:
                    decoded_parts.append(content.decode("latin1", errors="replace"))
            else:
                decoded_parts.append(str(content))
        return "".join(decoded_parts)

    def _clean_html_to_text(self, html_content):
        if not html_content:
            return ""
        
        text = re.sub(r'<(br|p|div|li|tr)[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        text = re.sub(r'</(p|div|li|tr)>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = html.unescape(text)
        text = re.sub(r'^[ \t]+|[ \t]+$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _parse_multipart_body(self, msg):
        """專門處理 multipart 郵件的輔助函數 (降低主要函數的認知複雜度)"""
        body = ""
        is_html = False
        
        for part in msg.walk():
            content_type = part.get_content_type()
            if "attachment" in str(part.get("Content-Disposition")):
                continue
                
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="replace")
                is_html = False
                break 
                
            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="replace")
                is_html = True
                
        return body, is_html


    def _get_body(self, msg):
        """主要獲取郵件內文的函數"""
        body = ""
        is_html = False
        
        # 將原本沉重的巢狀邏輯抽離
        if msg.is_multipart():
            body, is_html = self._parse_multipart_body(msg)
        else:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")
            if msg.get_content_type() == "text/html":
                is_html = True
        
        # 後續的 HTML 清理與長度限制邏輯維持不變
        if is_html or "<html" in body.lower() or "<body" in body.lower():
            body = self._clean_html_to_text(body)
        
        body = body.strip()
        from ..Gmail_config import MAX_EMAIL_BODY_LENGTH
        return (body[:MAX_EMAIL_BODY_LENGTH] + "...") if len(body) > MAX_EMAIL_BODY_LENGTH else body

    def _parse_latest_mail(self, raw_email, msg_id):
        msg = message_from_bytes(raw_email)
        
        message_id = msg.get("Message-ID", "")
        gmail_link = ""
        if message_id:
            import urllib.parse
            safe_id = urllib.parse.quote(message_id)
            gmail_link = f"https://mail.google.com/mail/u/0/#search/rfc822msgid%3A{safe_id}"

        return {
            "id": msg_id,
            "from": self.safe_decode(msg, "From"),
            "subject": self.safe_decode(msg, "Subject"),
            "body": self._get_body(msg),
            "date": msg.get("Date"),
            "link": gmail_link, 
            "raw": msg
        }