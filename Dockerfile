# 使用官方 Python 3.10 輕量版
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 1. 安裝系統工具、Chrome 依賴以及 execstack (修復 onnxruntime 用)
# libgl1, libglib2.0-0 是 ddddocr 必須的
# execstack 是用來解決 cannot enable executable stack 錯誤的
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    execstack \
    --no-install-recommends

# 2. 下載並安裝 Google Chrome 穩定版
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || apt-get -f install -y \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 3. 複製 requirements.txt 並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ★★★ 關鍵修正：強制清除 onnxruntime 的 executable stack 標記 ★★★
# 這行指令會找到所有 .so 檔並移除錯誤的權限標記，解決 Render 報錯
RUN find /usr/local/lib/python3.10/site-packages/onnxruntime -name "*.so" -exec execstack -c {} \;

# 4. 複製所有程式碼到容器內
COPY . .

# 5. 設定環境變數
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PORT=10000

# 6. 啟動指令 (使用 gunicorn 讓 Flask 背景執行，Bot 主程序執行)
# 如果你只跑 bot.py，且 bot.py 裡有 keep_alive()，則直接用 python bot.py 即可
CMD ["python", "bot.py"]