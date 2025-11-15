# Backend – FastAPI Service

This is the backend service for the Lexify project, built with **FastAPI** and **Python**.

## Prerequisites

- Python 3.9 or higher
- PowerShell (for Windows dev script)
- (Optional) `git` if you clone from a repository

## 1. Clone and navigate to backend
```bash
cd altai-tanba/backend
```

## 2. Create and activate a virtual environment

Create a virtual environment:
```bash
python -m venv .venv
```

Activate it (PowerShell, Windows):
```powershell
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the beginning of your terminal prompt.

For macOS/Linux:
```bash
source .venv/bin/activate
```

## 3. Install dependencies from requirements.txt

Install all required Python packages:
```bash
pip install -r requirements.txt
```

If you add new packages later, regenerate the file with:
```bash
pip freeze > requirements.txt
```

## 4. Configure environment variables (.env)

Create a file named `.env` in the backend folder (at the same level as `src/`) and fill it with the following configuration:
```env
# ==============================
# Database Configuration
# ==============================
DB_USER=
DB_PASSWORD=
DB_NAME=
DB_PORT=
DB_HOST=
PG_EMAIL=
PG_PASSWORD=
DATABASE_URL="

# ==============================
# Server Configuration
# ==============================
SECURITY_BACKEND_CORS_ORIGINS=
SECURITY_ALLOWED_HOSTS=
SERVER_PORT=
USE_STUB_ADAPTER=

# ==============================
# S3 / MinIO Configuration
# ==============================
S3_ACCESS_ENDPOINT=
S3_RESPONSE_ENDPOINT=
S3_REGION=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_BUCKET=
S3_IMAGE_PREFIX=
S3_AUDIO_PREFIX=
S3_PATH_STYLE=
```

The application will not start if any required environment variable is missing.

## 5. Run the development server

### Option A – Using the dev script (recommended on Windows)

From the backend folder:
```powershell
.\dev.ps1
```

This script will:
- Activate the `.venv` virtual environment (if it exists)
- Start the FastAPI server with reload using `python -m src.main`

By default, the server will be available at:
```
http://localhost:8080
```

Health check endpoint:
```
GET http://localhost:8080/ping
```

The server will also be available at:
```
http://localhost:8080
```

## 6. Verify the server

You can verify that the server is running with:
```bash
curl http://localhost:8080/ping
```

## API Documentation

Once the server is running, you can access the interactive API documentation at:


**Virtual environment activation issues on Windows:**

If you encounter execution policy errors, run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Missing dependencies:**

Ensure you've activated the virtual environment before installing packages. Try upgrading pip:
```bash
python -m pip install --upgrade pip
```

**Port already in use:**

Change the `SERVER_PORT` value in your `.env` file to use a different port.