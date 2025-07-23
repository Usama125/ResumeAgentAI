@echo off
REM ===============================================
REM AI RESUME BUILDER - START SERVER SCRIPT (Windows)
REM ===============================================

echo ============================================
echo    AI RESUME BUILDER - BACKEND SERVER    
echo ============================================
echo.

REM Check if we're in the right directory
if not exist "app\main.py" (
    echo [ERROR] app\main.py not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found. Please ensure you're in the correct directory.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo [WARNING] Virtual environment not found. Creating one...
    python -m venv venv
    echo [SUCCESS] Virtual environment created
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Installing/updating dependencies...
pip install -r requirements.txt

echo [INFO] Starting FastAPI server...
echo [INFO] Server will be available at: http://localhost:8000
echo [INFO] API Documentation: http://localhost:8000/docs
echo [INFO] Health Check: http://localhost:8000/health
echo.
echo [SUCCESS] Press Ctrl+C to stop the server
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause