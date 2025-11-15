$ErrorActionPreference = "Stop"

# Force UTF-8 encoding for Python (fixes Prisma schema.prisma Unicode issues on Windows)
$env:PYTHONUTF8 = "1"

# 1. Активируем виртуальное окружение, если есть .venv
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment .venv..."
    . .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠ .venv not found. Make sure dependencies are installed in the current Python environment."
}

# 2. Подтягиваем Prisma бинарники и генерируем Python-клиент (best-effort)
try {
    Write-Host "Fetching Prisma query engine (python) ..."
    prisma py fetch | Out-Null
} catch { Write-Host "(skip) prisma py fetch" }

try {
    Write-Host "Pushing Prisma schema to database ..."
    prisma db push | Out-Null
} catch { Write-Host "(skip) prisma db push" }

try {
    Write-Host "Generating Prisma client ..."
    prisma generate | Out-Null
} catch { Write-Host "(skip) prisma generate" }

# 3. Запускаем через main.py, который сам читает порт из .env
Write-Host "Starting FastAPI dev server..."
python -m src.main
