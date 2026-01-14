#!/bin/bash
# StockBuddy 快取清除腳本
# 使用方式: bash clear_cache.sh

echo "🧹 StockBuddy 快取清除工具"
echo "=========================="

# 1. 停止後端服務
echo ""
echo "⏹️  停止後端服務..."
pkill -f uvicorn 2>/dev/null
sleep 2

# 2. 清除 Python 快取
echo "🗑️  清除 Python 快取..."
cd ~/stockbuddy-backend 2>/dev/null || cd stockbuddy-backend 2>/dev/null
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
echo "   ✅ Python 快取已清除"

# 3. 清除 yfinance 快取
echo "🗑️  清除 yfinance 快取..."
rm -rf ~/.cache/py-yfinance 2>/dev/null
echo "   ✅ yfinance 快取已清除"

# 4. 清除 pip 快取（可選）
# rm -rf ~/.cache/pip 2>/dev/null

# 5. 重啟後端
echo ""
echo "🚀 重啟後端服務..."
cd ~/stockbuddy-backend 2>/dev/null || cd stockbuddy-backend 2>/dev/null
nohup uvicorn app.main:app --reload --port 8000 > /dev/null 2>&1 &
sleep 3

echo ""
echo "=========================="
echo "✅ 快取清除完成！"
echo ""
echo "📋 接下來請："
echo "   1. 在瀏覽器按 Ctrl+Shift+R 硬重新整理"
echo "   2. 點擊「更新」按鈕重新掃描"
echo ""
echo "💡 如果資料還是舊的，可能是 TWSE API 尚未更新"
echo "   (通常在交易日下午 3:30 後才有當日資料)"
