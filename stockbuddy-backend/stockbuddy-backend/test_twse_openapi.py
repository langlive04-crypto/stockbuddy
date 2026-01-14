"""
📈 TWSE OpenAPI 測試腳本

測試所有 API 端點是否正常運作
"""

import asyncio
import sys
sys.path.insert(0, '/home/claude/stockbuddy-backend')

from app.services.twse_openapi import TWSEOpenAPI


async def test_per_dividend():
    """測試本益比/殖利率 API"""
    print("\n" + "="*60)
    print("📊 測試 1: 本益比/殖利率 API")
    print("="*60)
    
    data = await TWSEOpenAPI.get_per_dividend_all()
    
    if data:
        print(f"✅ 成功取得 {len(data)} 檔股票資料")
        
        # 顯示幾個範例
        samples = ["2330", "2454", "2317", "2881", "1301"]
        print("\n範例資料：")
        for sid in samples:
            if sid in data:
                d = data[sid]
                print(f"  {sid} {d['name']}: P/E={d['pe_ratio']}, 殖利率={d['dividend_yield']}%, P/B={d['pb_ratio']}")
    else:
        print("❌ 無法取得資料")
    
    return len(data) if data else 0


async def test_daily_trading():
    """測試每日成交 API"""
    print("\n" + "="*60)
    print("📊 測試 2: 每日成交資訊 API")
    print("="*60)
    
    data = await TWSEOpenAPI.get_daily_trading_all()
    
    if data:
        print(f"✅ 成功取得 {len(data)} 檔股票資料")
        
        # 顯示幾個範例
        samples = ["2330", "2454", "2317"]
        print("\n範例資料：")
        for sid in samples:
            if sid in data:
                d = data[sid]
                print(f"  {sid} {d['name']}: 收盤={d['close']}, 漲跌={d['change']} ({d['change_percent']}%)")
    else:
        print("❌ 無法取得資料")
    
    return len(data) if data else 0


async def test_market_index():
    """測試大盤指數 API"""
    print("\n" + "="*60)
    print("📊 測試 3: 大盤指數 API")
    print("="*60)
    
    data = await TWSEOpenAPI.get_market_index()
    
    if data:
        print(f"✅ 成功取得 {len(data)} 項指數")
        
        for key, info in data.items():
            print(f"  {info['name']}: {info['value']} ({info['change_percent']}%)")
    else:
        print("❌ 無法取得資料（可能非交易時間）")
    
    return len(data) if data else 0


async def test_institutional():
    """測試三大法人 API"""
    print("\n" + "="*60)
    print("📊 測試 4: 三大法人買賣超 API")
    print("="*60)
    
    data = await TWSEOpenAPI.get_institutional_trading()
    
    if data:
        print(f"✅ 成功取得 {len(data)} 檔股票資料")
        
        # 顯示外資買超前 5 名
        sorted_data = sorted(
            [(k, v) for k, v in data.items() if v.get('foreign_net')],
            key=lambda x: x[1].get('foreign_net', 0),
            reverse=True
        )[:5]
        
        print("\n外資買超前 5 名：")
        for sid, d in sorted_data:
            print(f"  {sid} {d['name']}: 外資 {d['foreign_net']:+,} 張")
    else:
        print("⚠️ 無法取得資料（可能非交易日）")
    
    return len(data) if data else 0


async def test_margin():
    """測試融資融券 API"""
    print("\n" + "="*60)
    print("📊 測試 5: 融資融券 API")
    print("="*60)
    
    data = await TWSEOpenAPI.get_margin_trading()
    
    if data:
        print(f"✅ 成功取得 {len(data)} 檔股票資料")
        
        # 顯示幾個範例
        samples = ["2330", "2454"]
        print("\n範例資料：")
        for sid in samples:
            if sid in data:
                d = data[sid]
                print(f"  {sid}: 融資餘額={d['margin_balance']:,}, 融券餘額={d['short_balance']:,}")
    else:
        print("⚠️ 無法取得資料（可能非交易日）")
    
    return len(data) if data else 0


async def test_realtime():
    """測試即時報價 API"""
    print("\n" + "="*60)
    print("📊 測試 6: 即時報價 API")
    print("="*60)
    
    stock_ids = ["2330", "2454", "2317", "2881", "2882"]
    data = await TWSEOpenAPI.get_realtime_quotes(stock_ids)
    
    if data:
        print(f"✅ 成功取得 {len(data)} 檔即時報價")
        
        print("\n即時報價：")
        for sid in stock_ids:
            if sid in data:
                d = data[sid]
                price = d['price'] if d['price'] else '無交易'
                change = f"{d['change']:+.2f}" if d['change'] else '-'
                pct = f"({d['change_percent']:+.2f}%)" if d['change_percent'] else ''
                print(f"  {sid} {d['name']}: {price} {change} {pct}")
    else:
        print("⚠️ 無法取得資料（可能非交易時間）")
    
    return len(data) if data else 0


async def test_full_info():
    """測試綜合查詢 API"""
    print("\n" + "="*60)
    print("📊 測試 7: 綜合查詢 API（單一股票完整資訊）")
    print("="*60)
    
    stock_id = "2330"
    data = await TWSEOpenAPI.get_stock_full_info(stock_id)
    
    if data:
        print(f"✅ {stock_id} 完整資訊：")
        for key, value in data.items():
            if value is not None:
                print(f"  {key}: {value}")
    else:
        print("❌ 無法取得資料")
    
    return 1 if data else 0


async def test_all_summary():
    """測試全市場摘要 API"""
    print("\n" + "="*60)
    print("📊 測試 8: 全市場摘要 API")
    print("="*60)
    
    data = await TWSEOpenAPI.get_all_stocks_summary()
    
    if data:
        print(f"✅ 成功取得 {len(data)} 檔股票摘要")
        
        # 統計有完整資料的股票
        with_pe = sum(1 for d in data.values() if d.get('pe_ratio'))
        with_price = sum(1 for d in data.values() if d.get('price'))
        
        print(f"  有價格資料: {with_price} 檔")
        print(f"  有本益比資料: {with_pe} 檔")
    else:
        print("❌ 無法取得資料")
    
    return len(data) if data else 0


async def main():
    """執行所有測試"""
    print("\n" + "🚀" * 30)
    print("  TWSE OpenAPI 測試開始")
    print("🚀" * 30)
    
    results = {}
    
    # 執行所有測試
    results['本益比/殖利率'] = await test_per_dividend()
    results['每日成交'] = await test_daily_trading()
    results['大盤指數'] = await test_market_index()
    results['三大法人'] = await test_institutional()
    results['融資融券'] = await test_margin()
    results['即時報價'] = await test_realtime()
    results['綜合查詢'] = await test_full_info()
    results['全市場摘要'] = await test_all_summary()
    
    # 總結
    print("\n" + "="*60)
    print("📋 測試總結")
    print("="*60)
    
    for name, count in results.items():
        status = "✅" if count > 0 else "⚠️"
        print(f"  {status} {name}: {count} 筆資料")
    
    total_success = sum(1 for v in results.values() if v > 0)
    total_tests = len(results)
    
    print(f"\n📊 測試結果: {total_success}/{total_tests} 項成功")
    
    if total_success >= 6:
        print("🎉 TWSE OpenAPI 整合成功！")
    elif total_success >= 4:
        print("⚠️ 部分 API 可能因非交易時間無資料")
    else:
        print("❌ 請檢查網路連線或 API 狀態")


if __name__ == "__main__":
    asyncio.run(main())
