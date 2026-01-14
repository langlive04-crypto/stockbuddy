"""
FinMind API 測試腳本
在本地執行來驗證 API 是否正常

使用方式：
cd stockbuddy-backend
python test_finmind.py
"""

import httpx
import asyncio
from datetime import datetime, timedelta

API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0xMi0xNSAxODoxNToyNyIsInVzZXJfaWQiOiJxYXoxMjN3czEwIiwiaXAiOiIxMTguMTYxLjAuNjEifQ.viJTifXsYqiEoXqJh_xLBimflJA7n-7INzLnIjk4pao"
BASE_URL = "https://api.finmindtrade.com/api/v4/data"


async def test_single_stock():
    """測試單一股票查詢"""
    print("=" * 50)
    print("測試 1: 單一股票（台積電 2330）")
    print("=" * 50)
    
    # 使用過去幾天的日期（避免當天資料還沒更新）
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    
    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": "2330",
        "start_date": start_date,
        "end_date": end_date,
        "token": API_TOKEN,
    }
    
    print(f"請求參數: {params}")
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(BASE_URL, params=params)
        print(f"HTTP 狀態碼: {response.status_code}")
        
        data = response.json()
        print(f"API Status: {data.get('status')}")
        print(f"API Msg: {data.get('msg')}")
        print(f"資料筆數: {len(data.get('data', []))}")
        
        if data.get('data'):
            print(f"範例資料: {data['data'][0]}")
            return True
        return False


async def test_all_stocks():
    """測試全市場查詢"""
    print("\n" + "=" * 50)
    print("測試 2: 全市場掃描")
    print("=" * 50)
    
    # 嘗試最近幾天
    for days_ago in range(1, 6):
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        params = {
            "dataset": "TaiwanStockPrice",
            "start_date": date,
            "end_date": date,
            "token": API_TOKEN,
        }
        
        print(f"\n嘗試日期: {date}")
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(BASE_URL, params=params)
            print(f"  HTTP 狀態碼: {response.status_code}")
            
            if response.status_code != 200:
                print(f"  失敗，嘗試下一天...")
                continue
            
            data = response.json()
            print(f"  API Status: {data.get('status')}")
            
            if data.get('status') != 200:
                print(f"  API 錯誤: {data.get('msg')}")
                continue
            
            rows = data.get('data', [])
            print(f"  資料筆數: {len(rows)}")
            
            if len(rows) > 100:
                print(f"  ✅ 成功！取得 {len(rows)} 筆資料")
                # 統計股票數
                stock_ids = set(row.get('stock_id') for row in rows)
                print(f"  獨立股票數: {len(stock_ids)}")
                return True
    
    print("❌ 全市場查詢失敗")
    return False


async def test_institutional():
    """測試三大法人"""
    print("\n" + "=" * 50)
    print("測試 3: 三大法人買賣超（台積電 2330）")
    print("=" * 50)
    
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    
    params = {
        "dataset": "TaiwanStockInstitutionalInvestorsBuySell",
        "data_id": "2330",
        "start_date": start_date,
        "end_date": end_date,
        "token": API_TOKEN,
    }
    
    print(f"請求參數: {params}")
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(BASE_URL, params=params)
        print(f"HTTP 狀態碼: {response.status_code}")
        
        data = response.json()
        print(f"API Status: {data.get('status')}")
        print(f"API Msg: {data.get('msg')}")
        print(f"資料筆數: {len(data.get('data', []))}")
        
        if data.get('data'):
            print(f"範例資料: {data['data'][0]}")
            return True
        return False


async def test_margin():
    """測試融資融券"""
    print("\n" + "=" * 50)
    print("測試 4: 融資融券（台積電 2330）")
    print("=" * 50)
    
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    
    params = {
        "dataset": "TaiwanStockMarginPurchaseShortSale",
        "data_id": "2330",
        "start_date": start_date,
        "end_date": end_date,
        "token": API_TOKEN,
    }
    
    print(f"請求參數: {params}")
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(BASE_URL, params=params)
        print(f"HTTP 狀態碼: {response.status_code}")
        
        data = response.json()
        print(f"API Status: {data.get('status')}")
        print(f"API Msg: {data.get('msg')}")
        print(f"資料筆數: {len(data.get('data', []))}")
        
        if data.get('data'):
            print(f"範例資料: {data['data'][0]}")
            return True
        return False


async def main():
    print("🔍 FinMind API 測試開始")
    print(f"Token: {API_TOKEN[:20]}...")
    print()
    
    results = {
        "單一股票": await test_single_stock(),
        "全市場掃描": await test_all_stocks(),
        "三大法人": await test_institutional(),
        "融資融券": await test_margin(),
    }
    
    print("\n" + "=" * 50)
    print("測試結果總結")
    print("=" * 50)
    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{name}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
