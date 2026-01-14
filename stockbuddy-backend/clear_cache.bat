@echo off
REM StockBuddy 快取清除腳本 (Windows)
REM 使用方式: 雙擊執行或在 CMD 中執行

echo ==============================
echo   StockBuddy 快取清除工具
echo ==============================
echo.

REM 1. 停止後端服務
echo [1/4] 停止後端服務...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn*" 2>nul
taskkill /F /IM uvicorn.exe 2>nul
timeout /t 2 /nobreak >nul

REM 2. 清除 Python 快取
echo [2/4] 清除 Python 快取...
cd /d "%~dp0stockbuddy-backend" 2>nul
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
echo       Python 快取已清除

REM 3. 清除 yfinance 快取
echo [3/4] 清除 yfinance 快取...
rd /s /q "%USERPROFILE%\.cache\py-yfinance" 2>nul
echo       yfinance 快取已清除

REM 4. 重啟後端
echo [4/4] 重啟後端服務...
cd /d "%~dp0stockbuddy-backend"
start "StockBuddy Backend" cmd /c "uvicorn app.main:app --reload --port 8000"
timeout /t 3 /nobreak >nul

echo.
echo ==============================
echo   快取清除完成！
echo ==============================
echo.
echo 接下來請：
echo   1. 在瀏覽器按 Ctrl+Shift+R 硬重新整理
echo   2. 點擊「更新」按鈕重新掃描
echo.
echo 如果資料還是舊的，可能是 TWSE API 尚未更新
echo (通常在交易日下午 3:30 後才有當日資料)
echo.
pause
