from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def main():
    return '<h1>Bot is awake</h1>'

def run():
    app.run(host="0.0.0.0", port=8080)

# 修改這裡：增加一個參數 local_test，預設為 False
def keep_alive(local_test=False):
    # 如果是本機測試 (local_test=True)，就直接結束，不啟動伺服器
    if local_test:
        print("偵測到本機測試模式：已略過 Web Server 啟動 (避免 Ctrl+C 卡住)")
        return

    # 如果不是測試模式，才啟動伺服器
    server = Thread(target=run)
    server.start()