@echo off
REM FinGuard-RAG — One-Click Startup Script (Windows)
REM Run this from the project root: c:\amala_linux\Finguard_og\
REM Requires: Python venv already set up, no npm needed.

echo.
echo ============================================
echo   FinGuard-RAG Startup
echo   Backend : http://localhost:8000/docs
echo   Frontend: http://localhost:3000
echo ============================================
echo.

REM --- Terminal 1: FastAPI Backend ---
echo [1/2] Starting FastAPI backend on port 8000...
start "FinGuard Backend" cmd /k "call venv\Scripts\activate && uvicorn Finguard_rag.api.main:app --reload --port 8000"

REM Wait 3 seconds for backend to boot
timeout /t 3 /nobreak > nul

REM --- Terminal 2: Frontend (python HTTP server, no npm) ---
echo [2/2] Starting React frontend on port 3000...
start "FinGuard Frontend" cmd /k "cd frontend && python -m http.server 3000"

timeout /t 2 /nobreak > nul
echo.
echo Both servers starting...
echo   Backend API : http://localhost:8000
echo   Swagger UI  : http://localhost:8000/docs
echo   Frontend App: http://localhost:3000
echo.
echo Login with any demo user - no password needed.
echo Admin page available for CEO / compliance_officer roles.
echo.
pause
