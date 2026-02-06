FROM python:3.13-slim

# 設定工作目錄
WORKDIR /app

# 1. 更新系統並安裝 wget (下載工具)
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    --no-install-recommends

# 2. 直接下載並安裝 Google Chrome 穩定版 (.deb)
# 這種裝法會自動處理相依套件，且不需要 apt-key，避開 127 錯誤
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 3. 複製 requirements.txt 並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 複製所有程式碼到容器內
COPY . .

# 5. 設定 Chrome 路徑環境變數 (給 Python 程式讀取用)
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PORT=10000

# 6. 啟動指令 (請確認你的主程式檔名是 main.py 還是 bot.py)
CMD ["python", "bot.py"]