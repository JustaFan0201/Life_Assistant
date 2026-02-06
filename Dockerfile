# 使用官方 Python 3.9 輕量版 (相容性最佳)
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 1. 安裝系統工具、Chrome 依賴、以及資料庫編譯工具
# 增加了 libpq-dev, gcc, python3-dev 以確保資料庫套件能順利安裝
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

# 2. 下載並安裝 Google Chrome 穩定版
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || apt-get -f install -y \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 3. ★★★ 關鍵修正：使用 Debian Snapshot 永久連結下載 execstack ★★★
# 這個連結指向 2014 年的歷史備份，保證絕對存在，不會 404
RUN wget http://snapshot.debian.org/archive/debian/20141023T043132Z/pool/main/p/prelink/execstack_0.0.20131005-1+b10_amd64.deb \
    && dpkg -i execstack_0.0.20131005-1+b10_amd64.deb \
    && rm execstack_0.0.20131005-1+b10_amd64.deb

# 4. 複製 requirements.txt 並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. ★★★ 執行修復指令 ★★★
# 使用剛安裝好的 execstack 修復 onnxruntime 的權限問題
RUN find /usr/local/lib/python3.9/site-packages/onnxruntime -name "*.so" -exec execstack -c {} \;

# 6. 複製所有程式碼到容器內
COPY . .

# 7. 設定環境變數
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PORT=10000

# 8. 啟動指令
CMD ["python", "bot.py"]