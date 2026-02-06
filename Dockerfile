# 使用官方 Python 3.10 輕量版
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 1. 安裝系統工具與 Chrome 依賴
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

# 3. ★★★ 手動安裝 execstack (解決 apt 找不到的問題) ★★★
# 從 Debian 官方庫手動下載 .deb 檔並安裝
RUN wget http://ftp.us.debian.org/debian/pool/main/p/prelink/execstack_0.0.20131005-1+b10_amd64.deb \
    && dpkg -i execstack_0.0.20131005-1+b10_amd64.deb \
    && rm execstack_0.0.20131005-1+b10_amd64.deb

# 4. 複製 requirements.txt 並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. ★★★ 執行修復指令 ★★★
# 找出所有 onnxruntime 的 .so 檔，並清除 executable stack 標記
# 這樣 Render 就不會報錯了
RUN find /usr/local/lib/python3.10/site-packages/onnxruntime -name "*.so" -exec execstack -c {} \;

# 6. 複製所有程式碼到容器內
COPY . .

# 7. 設定環境變數
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PORT=10000

# 8. 啟動指令
CMD ["python", "bot.py"]