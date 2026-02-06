# ★★★ 改用 Python 3.9 以獲得最佳相容性 ★★★
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 1. 安裝系統工具與 Chrome/OpenCV 必要依賴
# libgl1, libglib2.0-0 是 ddddocr 必須的
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    --no-install-recommends

# 2. 下載並安裝 Google Chrome 穩定版
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
CMD ["python", "bot.py"]