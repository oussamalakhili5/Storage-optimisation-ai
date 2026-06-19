@echo off
echo ========================================================
echo Starting Storage Optimization AI (Local Dev Mode)
echo ========================================================
echo.
echo This mode runs the backend using a local JSON file for auth
echo and local CSV data for storage (No MongoDB/Docker required).
echo.

:: Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: Install backend dependencies if needed
echo [1/3] Checking backend dependencies...
cd backend
pip install fastapi uvicorn pandas numpy python-dotenv pydantic --quiet >nul 2>&1

:: Start backend server in a separate window
echo [2/3] Starting Backend Server...
start "Backend Server - Storage Optimization AI" cmd /k "python -m uvicorn dev_server:app --port 8000 --reload"
cd ..

:: Wait a moment for backend to start
timeout /t 3 /nobreak >nul

echo.
echo   Backend running at: http://127.0.0.1:8000
echo   Backend docs at:    http://127.0.0.1:8000/docs
echo.

:: Start frontend
echo [3/3] Starting Frontend Development Server...
cd frontend
call npm run dev
