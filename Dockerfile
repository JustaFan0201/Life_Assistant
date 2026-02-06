# 使用官方 Python 3.9 輕量版
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 1. 安裝系統工具、Chrome 依賴、以及資料庫編譯工具
# 移除了 wget (不需要抓 execstack 了)
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    libpq-dev \
    gcc \
    python3-dev \
    --no-install-recommends

# 2. 下載並安裝 Google Chrome 穩定版 (Chrome 還是要下載)
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || apt-get -f install -y \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 3. ★★★ 關鍵修改：直接複製本地的 execstack.deb ★★★
# 將專案資料夾裡的 execstack.deb 複製到 Docker 容器內
COPY execstack.deb .

# 4. 安裝 execstack
RUN dpkg -i execstack.deb && rm execstack.deb

# 5. 複製 requirements.txt 並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. ★★★ 執行修復指令 ★★★
# 使用剛安裝好的 execstack 修復 onnxruntime
RUN find /usr/local/lib/python3.9/site-packages/onnxruntime -name "*.so" -exec execstack -c {} \;

# 7. 複製所有程式碼到容器內
COPY . .

# 8. 設定環境變數
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PORT=10000

# 9. 啟動指令
CMD ["python", "bot.py"]