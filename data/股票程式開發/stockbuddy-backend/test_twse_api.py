#!/usr/bin/env python3
"""
TWSE OpenAPI 資料日期測試工具
用於檢查各 API 的資料更新狀態
"""

import requests
import json
from datetime import datetime

# 關閉 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_twse_apis():
    """測試 TWSE OpenAPI 各端點的資料日期"""
    
    print("=" * 60)
    print("🔍 TWSE OpenAPI 資料日期測試")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    apis = [
        {
            "name": "每日成交 (STOCK_DAY_ALL)",
            "url": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
            "date_field": "Date",
            "sample_field": "Code",
            "sample_value": "2330"
        },
        {
            "name": "本益比/殖利率 (BWIBBU_ALL)",
            "url": "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL",
            "date_field": "Date",
            "sample_field": "Code",
            "sample_value": "2330"
        },
        {
            "name": "大盤指數 (MI_INDEX)",
            "url": "https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX",
            "date_field": None,
            "sample_field": "指數",
            "sample_value": "發行量加權股價指數"
        },
    ]
    
    results = []
    
    for api in apis:
        print(f"\n📊 測試: {api['name']}")
        print(f"   URL: {api['url']}")
        
        try:
            resp = requests.get(api['url'], verify=False, timeout=30)
            
            if resp.status_code != 200:
                print(f"   ❌ HTTP 錯誤: {resp.status_code}")
                continue
            
            data = resp.json()
            
            if not data:
                print(f"   ⚠️ 無資料")
                continue
            
            print(f"   ✅ 取得 {len(data)} 筆資料")
            
            # 取得第一筆資料的日期
            first_item = data[0]
            date_value = first_item.get(api['date_field'], "無日期欄位")
            
            # 轉換民國年格式
            if date_value and len(str(date_value)) == 7:
                try:
                    roc_year = int(str(date_value)[:3])
                    month = str(date_value)[3:5]
                    day = str(date_value)[5:7]
                    ad_year = roc_year + 1911
                    date_display = f"{ad_year}/{month}/{day}"
                except:
                    date_display = date_value
            else:
                date_display = date_value
            
            print(f"   📅 資料日期: {date_value} → {date_display}")
            
            # 找特定股票的資料
            sample_data = None
            for item in data:
                if item.get(api['sample_field']) == api['sample_value']:
                    sample_data = item
                    break
            
            if sample_data:
                print(f"   📌 範例資料 ({api['sample_value']}):")
                # 只顯示重要欄位
                important_fields = ['Code', 'Name', 'ClosingPrice', 'Change', 'Date', 
                                   'PEratio', 'DividendYield', '指數', '收盤指數', '漲跌點數']
                for key, value in sample_data.items():
                    if key in important_fields:
                        print(f"      {key}: {value}")
            
            results.append({
                "api": api['name'],
                "status": "OK",
                "date": date_display,
                "count": len(data)
            })
            
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")
            results.append({
                "api": api['name'],
                "status": "ERROR",
                "error": str(e)
            })
    
    # 總結
    print("\n" + "=" * 60)
    print("📋 測試結果總結")
    print("=" * 60)
    
    today = datetime.now()
    today_roc = f"{today.year - 1911}{today.month:02d}{today.day:02d}"
    today_display = today.strftime("%Y/%m/%d")
    
    print(f"\n📅 今天日期: {today_display} (民國 {today_roc})")
    print()
    
    for r in results:
        if r['status'] == 'OK':
            is_today = today_display in r.get('date', '')
            status_icon = "✅" if is_today else "⚠️"
            status_text = "已更新" if is_today else "尚未更新"
            print(f"{status_icon} {r['api']}: {r['date']} ({status_text})")
        else:
            print(f"❌ {r['api']}: 錯誤 - {r.get('error', 'unknown')}")
    
    print("\n" + "=" * 60)
    print("💡 說明:")
    print("   - STOCK_DAY_ALL: 通常 16:30 後更新")
    print("   - BWIBBU_ALL: 通常 18:00-19:00 後更新")
    print("   - 如果顯示昨天日期，表示 TWSE 尚未更新")
    print("=" * 60)

if __name__ == "__main__":
    test_twse_apis()
