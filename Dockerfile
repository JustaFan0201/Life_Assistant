# ★★★ 關鍵 1: 改用 python:3.9-bullseye (Debian 11) ★★★
# 這個版本的 Linux 允許我們安裝 execstack 工具
FROM python:3.9-bullseye

# 設定工作目錄
WORKDIR /app

# 1. 安裝系統工具
# libgl1, libglib2.0-0 是 ddddocr 必須的
# execstack 是用來修復 onnxruntime 權限問題的
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

# 4. ★★★ 關鍵 2: 執行修復指令 ★★★
# 找出所有 onnxruntime 的 .so 檔，並強制移除「需要執行堆疊」的標記
# 這樣 Render 就不會報錯，可以正常載入了
RUN find /usr/local/lib/python3.9/site-packages/onnxruntime -name "*.so" -exec execstack -c {} \;

# 5. 複製所有程式碼到容器內
COPY . .

# 6. 設定環境變數
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PORT=10000

# 7. 啟動指令
CMD ["python", "bot.py"]