# 維持使用 Debian 11 (Bullseye) 以確保 Python 套件相容性
FROM python:3.9-bullseye

# 設定工作目錄
WORKDIR /app

# 1. 安裝系統基本工具與 Chrome/OpenCV 依賴
# 注意：這裡我們先不裝 execstack，因為 apt 找不到
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    --no-install-recommends

# 2. ★★★ 手動下載並安裝 execstack ★★★
# 我們直接從 Debian 的歷史庫抓這個工具，繞過 apt
RUN wget http://ftp.de.debian.org/debian/pool/main/p/prelink/execstack_0.0.20131005-1+b10_amd64.deb \
    && dpkg -i execstack_0.0.20131005-1+b10_amd64.deb \
    && rm execstack_0.0.20131005-1+b10_amd64.deb

# 3. 下載並安裝 Google Chrome 穩定版
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || apt-get -f install -y \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 4. 複製 requirements.txt 並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. ★★★ 執行修復指令 ★★★
# 找出所有 onnxruntime 的 .so 檔，並強制移除「需要執行堆疊」的標記
# 確保路徑是正確的 (Debian/Python 3.9 的路徑通常在這裡)
RUN find /usr/local/lib/python3.9/site-packages/onnxruntime -name "*.so" -exec execstack -c {} \;

# 6. 複製所有程式碼到容器內
COPY . .

# 7. 設定環境變數
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PORT=10000

# 8. 啟動指令
CMD ["python", "bot.py"]