@echo off
title StockBuddy Backend V10.21
color 0A

echo.
echo  ========================================
echo     StockBuddy Backend V10.21
echo  ========================================
echo.

cd /d "%~dp0stockbuddy-backend"

echo  API Docs: http://localhost:8000/docs
echo.
echo  New API Endpoints (V10.17-V10.21):
echo  - /api/stocks/screener/*      Stock Screener
echo  - /api/stocks/compare/*       Stock Comparison
echo  - /api/stocks/alerts/*        Price Alerts
echo  - /api/stocks/transactions/*  Transaction Manager
echo  - /api/stocks/categories/*    Watchlist Categories
echo.
echo  ========================================
echo.

python -m uvicorn app.main:app --reload --port 8000

pause
