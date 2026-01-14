@echo off
title StockBuddy Service Stopper
color 0C

echo.
echo  ========================================
echo     StockBuddy Service Stopper
echo  ========================================
echo.

echo  [INFO] Stopping all StockBuddy services...
echo.

echo  [1/2] Stopping frontend (Node.js)...
taskkill /f /im node.exe >nul 2>nul
if %errorlevel%==0 (
    echo        Node.js process stopped
) else (
    echo        No running Node.js process found
)

echo  [2/2] Stopping backend (Python)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>nul
)
echo        Attempted to stop service on port 8000

echo.
echo  ========================================
echo     Services Stopped
echo  ========================================
echo.

pause
