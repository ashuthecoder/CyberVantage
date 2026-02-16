@echo off
setlocal

set ROOT_DIR=%~dp0

cd /d "%ROOT_DIR%frontend"
call npm install
if errorlevel 1 exit /b 1
call npm run build
if errorlevel 1 exit /b 1

cd /d "%ROOT_DIR%"
py -m pip install -r requirements-fastapi.txt
if errorlevel 1 exit /b 1
py -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
