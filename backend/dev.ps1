$ErrorActionPreference = "Stop"

# 1. Активируем виртуальное окружение, если есть .venv
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment .venv..."
    . .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠ .venv not found. Make sure dependencies are installed in the current Python environment."
}

# 2. Запускаем через main.py, который сам читает порт из .env
Write-Host "Starting FastAPI dev server..."
python -m src.main
