# StockBuddy Backend API

智能選股助手後端 API 服務

## 🚀 快速開始

### 1. 安裝相依套件
```bash
cd stockbuddy-backend
pip install -r requirements.txt
```

### 2. 啟動 API 伺服器
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 開啟 API 文件
瀏覽器打開：http://localhost:8000/docs

---

## 📊 資料來源

系統會自動選擇可用的資料源（優先順序）：

| 優先級 | 資料源 | 說明 |
|--------|--------|------|
| 1 | **yfinance** | Yahoo Finance，最即時 |
| 2 | **GitHub tw_stocker** | 每天更新的開源資料庫 |
| 3 | **Mock Data** | 模擬資料（開發測試用）|

### GitHub 資料來源
感謝 [voidful/tw_stocker](https://github.com/voidful/tw_stocker) 專案提供每日更新的台股資料！

```python
# 資料格式
url = "https://raw.githubusercontent.com/voidful/tw_stocker/main/data/2330.csv"
```

---

## 📁 專案結構

```
stockbuddy-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 主程式
│   ├── routers/
│   │   ├── __init__.py
│   │   └── stocks.py        # 股票相關 API 路由
│   ├── services/
│   │   ├── __init__.py
│   │   ├── stock_data.py    # 真實股票資料服務 (yfinance)
│   │   ├── mock_data.py     # Mock 資料服務 (開發用)
│   │   ├── twse_api.py      # 台灣證交所 API (備用)
│   │   └── technical_analysis.py  # 技術分析模組
│   └── models/
│       ├── __init__.py
│       └── schemas.py       # Pydantic 資料模型
├── requirements.txt
├── test_api.py              # 測試腳本
└── README.md
```

---

## 🔌 API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/` | GET | API 首頁資訊 |
| `/health` | GET | 健康檢查 |
| `/api/stocks/info/{stock_id}` | GET | 個股即時資訊 |
| `/api/stocks/history/{stock_id}` | GET | 歷史 K 線資料 |
| `/api/stocks/analysis/{stock_id}` | GET | 技術分析 |
| `/api/stocks/market` | GET | 大盤概況 |
| `/api/stocks/recommend` | GET | AI 推薦股票 |
| `/api/stocks/search?q=xxx` | GET | 搜尋股票 |

---

## 📊 回應範例

### AI 推薦 `/api/stocks/recommend`
```json
{
  "updated_at": "2024-12-13T14:30:00",
  "market": {
    "value": 23150.55,
    "change_percent": 0.85,
    "mood": "偏多"
  },
  "count": 5,
  "recommendations": [
    {
      "stock_id": "2330",
      "name": "台積電",
      "price": 580,
      "change_percent": 2.5,
      "confidence": 85,
      "signal": "買進",
      "reason": "股價站上月線，RSI 處於健康區間，MACD 維持多方格局",
      "action": "建議價位 $568.4-580",
      "stop_loss": 551,
      "target": 638,
      "details": {
        "technical": { "score": 82, "ma": "多頭排列", "rsi": 58, "macd": "多方" },
        "fundamental": { "score": 60, "note": "開發中" },
        "news": { "score": 50, "sentiment": "中性" },
        "chip": { "score": 50, "note": "開發中" }
      }
    }
  ]
}
```

---

## ⚙️ 切換資料來源

在 `app/services/mock_data.py` 中：

```python
USE_MOCK = True   # 開發模式：使用模擬資料
USE_MOCK = False  # 正式模式：使用真實 API (需網路)
```

---

## 🔧 技術分析指標

目前支援的技術指標：

- **均線 (MA)**: MA5, MA20, MA60
- **RSI**: 相對強弱指標
- **MACD**: 指數平滑異同移動平均線
- **布林通道**: Bollinger Bands
- **支撐/壓力位**: 近期高低點
- **成交量分析**: 量比

---

## 📝 待開發功能

- [ ] 三大法人即時買賣超（需串接證交所）
- [ ] 新聞情緒分析（串接新聞 API + Claude AI）
- [ ] 財報基本面資料（串接公開資訊觀測站）
- [ ] 用戶觀察清單（需資料庫）
- [ ] 推播通知

---

## ⚠️ 免責聲明

本工具僅供參考，不構成投資建議。
投資有風險，過去績效不代表未來表現。
使用者需自行承擔投資決策責任。
