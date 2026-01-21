import os
from aiosmtplib import SMTP
from email.message import EmailMessage

class EmailTools:
    def __init__(self):
        self.host = "smtp.gmail.com"
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