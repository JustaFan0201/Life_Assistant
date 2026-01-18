# 使用官方 Python 輕量版映像檔
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 1. 安裝系統工具與 Chrome 依賴
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. 安裝 Google Chrome (穩定版)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 3. 複製 requirements.txt 並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 複製所有程式碼到容器內
COPY . .

# 5. 設定環境變數，讓程式知道 Chrome 在哪 (保險起見)
ENV GOOGLE_CHROME_BIN=/usr/bin/google-chrome-stable

# 6. 啟動指令 (請將 main.py 改成你真正的機器人啟動檔案)
CMD ["python", "bot.py"]