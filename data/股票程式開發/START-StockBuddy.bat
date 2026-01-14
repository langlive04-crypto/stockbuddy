@echo off
chcp 65001 >nul 2>nul
title StockBuddy V10.21 Quick Start
color 0E

echo.
echo  ========================================
echo     StockBuddy V10.21 Quick Start
echo  ========================================
echo.

pushd "%~dp0"

if not exist "stockbuddy-backend" (
    echo  [ERROR] stockbuddy-backend not found!
    pause
    exit /b 1
)

if not exist "stockbuddy-frontend" (
    echo  [ERROR] stockbuddy-frontend not found!
    pause
    exit /b 1
)

echo  [1/3] Starting backend...
pushd stockbuddy-backend
start "StockBuddy Backend" cmd /k "color 0A && python -m uvicorn app.main:app --reload --port 8000"
popd

timeout /t 3 /nobreak > nul

echo  [2/3] Starting frontend...
pushd stockbuddy-frontend
start "StockBuddy Frontend" cmd /k "color 0B && npm run dev"
popd

timeout /t 5 /nobreak > nul

echo  [3/3] Opening browser...
start http://localhost:3000

echo.
echo  ========================================
echo     Started Successfully!
echo  ========================================
echo.
echo  Frontend: http://localhost:3000
echo  API Docs: http://localhost:8000/docs
echo.
echo  Press any key to close...
pause > nul
popd
