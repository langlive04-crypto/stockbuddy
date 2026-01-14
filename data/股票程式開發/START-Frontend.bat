@echo off
title StockBuddy Frontend V10.21
color 0B

echo.
echo  ========================================
echo     StockBuddy Frontend V10.21
echo  ========================================
echo.

cd /d "%~dp0stockbuddy-frontend"

echo  URL: http://localhost:3000
echo.
echo  New Features (V10.17-V10.21):
echo  - Stock Screener
echo  - Stock Comparison (Radar Chart)
echo  - Price Alerts (Browser Notifications)
echo  - Transaction Manager
echo  - Watchlist Categories
echo.
echo  ========================================
echo.

npm run dev

pause
