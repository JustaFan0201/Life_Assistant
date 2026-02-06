# 使用官方 Python 3.10 輕量版
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 1. 安裝系統工具與 Chrome/OpenCV 必要依賴
# libgl1, libglib2.0-0 是 ddddocr (opencv) 必須的
# gnupg, curl, wget 是下載工具
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    --no-install-recommends

# 2. 下載並安裝 Google Chrome 穩定版
# 使用 dpkg 安裝，並用 apt-get -f install 修復缺少的 Chrome 依賴 (如字型庫)
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || apt-get -f install -y \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 3. 複製 requirements.txt 並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 複製所有程式碼到容器內
COPY . .

# 5. 設定環境變數
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PORT=10000

# 6. 啟動指令
# 如果你有加 gunicorn，建議讓它在背景跑 keep_alive，或者保持你原本的 bot.py
# 這裡維持原本的 CMD 即可，只要你的 bot.py 裡有啟動 Flask
CMD ["python", "bot.py"]