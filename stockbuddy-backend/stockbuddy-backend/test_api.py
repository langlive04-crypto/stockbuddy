"""
API 功能測試腳本 - Mock 版本
"""

import asyncio
import sys
sys.path.insert(0, '/home/claude/stockbuddy-backend')

from app.services.mock_data import MockStockDataService as StockDataService
from app.services.technical_analysis import TechnicalAnalysis


async def test_stock_data_service():
    """測試股票資料服務"""
    print("=" * 60)
    print("🧪 測試股票資料服務 (Mock 模式)")
    print("=" * 60)
    
    try:
        # 1. 測試取得大盤指數
        print("\n📊 測試取得大盤指數...")
        index = await StockDataService.get_market_index()
        if index:
            print(f"  ✅ 成功！")
            print(f"  加權指數: {index['value']:,.2f}")
            print(f"  漲跌: {index['change']:+.2f} ({index['change_percent']:+.2f}%)")
        else:
            print("  ❌ 失敗")

        # 2. 測試取得個股資訊
        print("\n📈 測試取得個股資訊 (2330 台積電)...")
        info = await StockDataService.get_stock_info("2330")
        if info:
            print(f"  ✅ 成功！")
            print(f"  股票: {info['name']} ({info['stock_id']})")
            print(f"  收盤價: ${info['close']}")
            print(f"  漲跌: {info['change']:+.2f} ({info['change_percent']:+.2f}%)")
        else:
            print("  ❌ 失敗")

        # 3. 測試取得歷史資料
        print("\n📉 測試取得歷史K線 (2330, 3個月)...")
        history = await StockDataService.get_stock_history("2330", months=3)
        if history:
            print(f"  ✅ 成功！取得 {len(history)} 筆資料")
            print(f"  最新: {history[-1]['date']} 收盤 ${history[-1]['close']}")
            print(f"  最舊: {history[0]['date']} 收盤 ${history[0]['close']}")
        else:
            print("  ❌ 失敗")

        # 4. 測試技術分析
        if history and len(history) >= 60:
            print("\n🔬 測試技術分析...")
            analysis = TechnicalAnalysis.full_analysis(history)
            print(f"  ✅ 成功！")
            print(f"  現價: ${analysis['current_price']}")
            print(f"  均線: MA5={analysis['ma']['ma5']}, MA20={analysis['ma']['ma20']}, MA60={analysis['ma']['ma60']}")
            print(f"  RSI: {analysis['rsi']['value']} ({analysis['rsi']['status']})")
            print(f"  MACD: {analysis['macd']['signal']} ({analysis['macd']['momentum']})")
            print(f"  趨勢: {analysis['trend']['trend']} ({analysis['trend']['trend_desc']})")
            print(f"  📊 綜合評分: {analysis['overall_score']}/100")
            print(f"  📝 摘要: {analysis['summary']}")

        # 5. 測試籌碼資料
        print("\n🏦 測試三大法人資料...")
        chip = await StockDataService.get_institutional_data("2330")
        print(f"  ✅ 成功！")
        print(f"  外資: {chip['foreign_net']:+,} 張")
        print(f"  投信: {chip['investment_net']:+,} 張")
        print(f"  合計: {chip['total_net']:+,} 張")

    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 測試完成")
    print("=" * 60)


async def test_recommendations():
    """測試推薦功能"""
    print("\n" + "=" * 60)
    print("🎯 測試 AI 推薦股票")
    print("=" * 60)
    
    stocks = ["2330", "2454", "2317", "2881", "2303"]
    
    for stock_id in stocks:
        info = await StockDataService.get_stock_info(stock_id)
        history = await StockDataService.get_stock_history(stock_id, months=3)
        
        if info and history and len(history) >= 60:
            analysis = TechnicalAnalysis.full_analysis(history)
            score = analysis["overall_score"]
            
            if score >= 75:
                signal = "🔴 買進"
            elif score >= 60:
                signal = "🟡 持有"
            elif score >= 45:
                signal = "⚪ 觀望"
            else:
                signal = "🟢 減碼"
            
            print(f"\n{info['name']} ({stock_id})")
            print(f"  價格: ${info['close']} ({info['change_percent']:+.2f}%)")
            print(f"  評分: {score}/100 → {signal}")
            print(f"  摘要: {analysis['summary']}")


if __name__ == "__main__":
    print("\n🚀 StockBuddy API 測試\n")
    asyncio.run(test_stock_data_service())
    asyncio.run(test_recommendations())
