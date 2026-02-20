@echo off
setlocal EnableExtensions

set ROOT_DIR=%~dp0

set "BACKEND_URL=http://localhost:8000"
set "FRONTEND_URL=%BACKEND_URL%"
if /I "%~1"=="dev" set "FRONTEND_URL=http://localhost:5173"

cd /d "%ROOT_DIR%frontend"
call npm install
if errorlevel 1 exit /b 1

REM --- dev mode: run Vite dev server in a new window; default: build production assets ---
if /I "%~1"=="dev" (
  echo Starting frontend dev server in a new window...
  start "Frontend" cmd /k "cd /d \"%ROOT_DIR%frontend\" && npm run dev"
  echo Frontend dev server will usually be available at %FRONTEND_URL%
) else (
  call npm run build
  if errorlevel 1 exit /b 1
  echo Frontend built. Production files are in frontend\dist
)

cd /d "%ROOT_DIR%"

REM --- detect Python executable (try `python`, then `py`) ---
where python >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PY_EXE=python"
) else (
  where py >nul 2>&1
  if %ERRORLEVEL%==0 (
    set "PY_EXE=py"
  ) else (
    echo Python is not installed or not on PATH. Install Python 3.8+ or add `python`/`py` to PATH.
    exit /b 1
  )
)

"%PY_EXE%" -m pip install -r requirements-fastapi.txt
if errorlevel 1 exit /b 1

echo.
echo ===================== CyberVantage URLs =====================
echo App (Frontend): %FRONTEND_URL%
echo API Docs:       %BACKEND_URL%/docs
echo API Health:     %BACKEND_URL%/api/health
echo =============================================================
echo.
echo When you see "Uvicorn running on ...", open the App URL above.
"%PY_EXE%" -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
