# 使用官方 Python 3.10 輕量版
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 1. 安裝系統工具與 Chrome 依賴
# ★★★ 修改點：這裡移除了 execstack，因為 apt 抓不到 ★★★
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
    && rm google-chrome-stable_current_amd64.deb

# 3. ★★★ 關鍵修改：手動下載並安裝 execstack ★★★
# 從 Debian 舊倉庫下載 execstack 安裝包
RUN wget http://ftp.de.debian.org/debian/pool/main/p/prelink/execstack_0.0.20131005-1+b10_amd64.deb \
    && dpkg -i execstack_0.0.20131005-1+b10_amd64.deb \
    && rm execstack_0.0.20131005-1+b10_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 4. 複製 requirements.txt 並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. ★★★ 修復 onnxruntime 權限 ★★★
# 現在 execstack 已經安裝好了，可以執行這個修復指令
RUN find /usr/local/lib/python3.10/site-packages/onnxruntime -name "*.so" -exec execstack -c {} \;

# 6. 複製所有程式碼到容器內
COPY . .

# 7. 設定環境變數
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PORT=10000

# 8. 啟動指令
CMD ["python", "bot.py"]