from flask import Flask
from waitress import serve
from threading import Thread

app = Flask('')

@app.route('/')
def main():
    return '<h1>Bot is awake</h1>'

def run(host="127.0.0.1"):
    serve(app, host=host, port=8080)

# 修改這裡：增加一個參數 local_test，預設為 False
def keep_alive(local_test=False):
    # 如果是本機測試 (local_test=True)，就直接結束，不啟動伺服器
    if local_test:
        print("偵測到本機測試模式：已略過 Web Server 啟動 (避免 Ctrl+C 卡住)")
        return
    
    target_host = "0.0.0.0"

    # 如果不是測試模式，才啟動伺服器
    server = Thread(target=run, args=(target_host,))
    server.start()