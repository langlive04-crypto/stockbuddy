"""
StockBuddy API 測試腳本 V10.15
驗證所有 API 端點功能

執行方式：
1. 先啟動後端：python -m uvicorn app.main:app --reload
2. 在另一個終端執行：python test_api.py
"""

import asyncio
import httpx
from datetime import datetime

API_BASE = "http://localhost:8000"

# 測試結果統計
results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}


async def test_endpoint(name: str, method: str, url: str, expected_status: int = 200):
    """測試單一端點"""
    global results

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if method == "GET":
                response = await client.get(f"{API_BASE}{url}")
            elif method == "POST":
                response = await client.post(f"{API_BASE}{url}")
            else:
                print(f"  ⚠️  不支援的方法: {method}")
                return False

            if response.status_code == expected_status:
                # 檢查 JSON 回應
                try:
                    data = response.json()
                    success = data.get("success", True) if isinstance(data, dict) else True

                    if success or expected_status != 200:
                        print(f"  ✅ {name}: 通過")
                        results["passed"] += 1
                        return True
                    else:
                        error_msg = data.get("error", "未知錯誤")
                        print(f"  ❌ {name}: 失敗 - {error_msg}")
                        results["failed"] += 1
                        results["errors"].append(f"{name}: {error_msg}")
                        return False
                except:
                    # 可能是檔案下載
                    print(f"  ✅ {name}: 通過 (非 JSON 回應)")
                    results["passed"] += 1
                    return True
            else:
                print(f"  ❌ {name}: HTTP {response.status_code}")
                results["failed"] += 1
                results["errors"].append(f"{name}: HTTP {response.status_code}")
                return False

    except httpx.ConnectError:
        print(f"  ❌ {name}: 無法連接伺服器")
        results["failed"] += 1
        results["errors"].append(f"{name}: 無法連接")
        return False
    except Exception as e:
        print(f"  ❌ {name}: {str(e)[:50]}")
        results["failed"] += 1
        results["errors"].append(f"{name}: {str(e)[:50]}")
        return False


async def main():
    print("=" * 60)
    print("StockBuddy API V10.15 測試")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ========== 基本端點 ==========
    print("\n📌 基本端點")
    await test_endpoint("首頁", "GET", "/")
    await test_endpoint("健康檢查", "GET", "/health")

    # ========== 股票資料 API ==========
    print("\n📊 股票資料 API")
    await test_endpoint("股票資訊 (2330)", "GET", "/api/stocks/info/2330")
    await test_endpoint("歷史K線 (2330)", "GET", "/api/stocks/history/2330")
    await test_endpoint("搜尋股票", "GET", "/api/stocks/search?q=台積")
    await test_endpoint("大盤概況", "GET", "/api/stocks/market")

    # ========== 技術分析 API ==========
    print("\n📈 技術分析 API")
    await test_endpoint("技術分析 (2330)", "GET", "/api/stocks/analysis/2330")

    # ========== 三大法人 API ==========
    print("\n🏦 三大法人 API")
    await test_endpoint("法人買賣超 (全市場)", "GET", "/api/stocks/institutional")
    await test_endpoint("個股法人 (2330)", "GET", "/api/stocks/institutional/2330")
    await test_endpoint("法人追蹤 (2330)", "GET", "/api/stocks/institutional-tracking/2330?days=20")

    # ========== AI 推薦 API ==========
    print("\n🤖 AI 推薦 API")
    await test_endpoint("AI 推薦", "GET", "/api/stocks/recommend")

    # ========== V10.15 新增 - 績效分析 ==========
    print("\n📊 績效分析 API (V10.15)")
    await test_endpoint("績效分析 (2330)", "GET", "/api/stocks/performance/2330?months=6")
    await test_endpoint("月報酬熱力圖 (2330)", "GET", "/api/stocks/performance/2330/monthly-heatmap?years=2")
    await test_endpoint("風險指標 (2330)", "GET", "/api/stocks/performance/2330/risk-metrics?months=6")

    # ========== V10.15 新增 - 匯出功能 ==========
    print("\n📤 匯出功能 API (V10.15)")
    await test_endpoint("匯出推薦 CSV", "GET", "/api/stocks/export/recommendations/csv")
    await test_endpoint("匯出推薦 Excel", "GET", "/api/stocks/export/recommendations/excel")

    # ========== V10.15 新增 - 櫃買股票 ==========
    print("\n🏢 櫃買股票 API (V10.15)")
    await test_endpoint("上櫃股票總覽", "GET", "/api/stocks/otc/all")
    await test_endpoint("市場類型判斷 (2330)", "GET", "/api/stocks/market-type/2330")
    await test_endpoint("市場類型判斷 (6488)", "GET", "/api/stocks/market-type/6488")

    # ========== V10.15 新增 - 資料狀態 ==========
    print("\n⏰ 資料狀態 API (V10.15)")
    await test_endpoint("資料更新狀態", "GET", "/api/stocks/data-status")

    # ========== 回測 API ==========
    print("\n🔄 回測 API")
    await test_endpoint("回測 (2330)", "GET", "/api/stocks/backtest/2330?months=6&strategy=combined")

    # ========== 結果摘要 ==========
    print("\n" + "=" * 60)
    print("測試結果摘要")
    print("=" * 60)
    total = results['passed'] + results['failed']
    print(f"✅ 通過: {results['passed']}")
    print(f"❌ 失敗: {results['failed']}")
    if total > 0:
        print(f"📊 通過率: {results['passed'] / total * 100:.1f}%")

    if results["errors"]:
        print("\n❌ 失敗的測試:")
        for error in results["errors"]:
            print(f"  - {error}")

    print("\n" + "=" * 60)

    return results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
