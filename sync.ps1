# Discord Bot - Environment Sync Script for Windows (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Discord Bot Environment Sync" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 檢查是否有安裝 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[INFO] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.13 or higher from https://www.python.org/"
    Read-Host "Press Enter to exit"
    exit 1
}

# 2. 建立虛擬環境 (.venv)
Write-Host ""
Write-Host "[INFO] Setting up virtual environment..." -ForegroundColor Cyan

if (Test-Path ".venv") {
    Write-Host "[INFO] Virtual environment already exists (.venv)" -ForegroundColor Yellow
} else {
    Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Host "[INFO] Virtual environment created" -ForegroundColor Green
}

# 3. 啟動虛擬環境 (僅在此腳本執行期間有效)
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# 4. 安裝 requirements.txt
Write-Host "[INFO] Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

if (Test-Path "requirements.txt") {
    Write-Host "[INFO] Installing dependencies from requirements.txt..." -ForegroundColor Cyan
    pip install -r requirements.txt

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "[WARNING] requirements.txt not found! Skipping dependency install." -ForegroundColor Yellow
}

# 5. 完成提示
Write-Host ""
Write-Host "[SUCCESS] Environment synced successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the environment (Run this in terminal):" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "To run the bot:" -ForegroundColor Cyan
Write-Host "  python bot.py"
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Sync complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"