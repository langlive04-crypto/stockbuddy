# 📈 StockBuddy V10.7 更新 - TWSE OpenAPI 整合

> 更新日期：2024/12/21
> 版本：V10.7

---

## 🆕 新增功能

### TWSE OpenAPI 整合

整合台灣證交所官方 OpenAPI，**不需要 API Key**，可直接取得即時資料！

#### 新增 API 端點

| 端點 | 說明 | 資料來源 |
|------|------|----------|
| `/api/stocks/twse/per-dividend` | 全市場本益比、殖利率、淨值比 | TWSE OpenAPI |
| `/api/stocks/twse/daily-trading` | 全市場每日成交資訊 | TWSE OpenAPI |
| `/api/stocks/twse/market-index` | 大盤指數（加權、台50等） | TWSE OpenAPI |
| `/api/stocks/twse/institutional` | 三大法人買賣超 | TWSE 官方 |
| `/api/stocks/twse/margin` | 融資融券資料 | TWSE 官方 |
| `/api/stocks/twse/realtime?stock_ids=2330,2454` | 即時報價 | TWSE 即時 |
| `/api/stocks/twse/stock/{stock_id}` | 單一股票完整資訊 | 整合多個 API |
| `/api/stocks/twse/all-summary` | 全市場摘要（最常用） | 整合多個 API |

---

## 📊 TWSE OpenAPI 資料說明

### 1. 本益比/殖利率 (`/twse/per-dividend`)

```json
{
  "2330": {
    "stock_id": "2330",
    "name": "台積電",
    "pe_ratio": 23.37,
    "dividend_yield": 1.19,
    "pb_ratio": 7.42
  }
}
```

### 2. 每日成交 (`/twse/daily-trading`)

```json
{
  "2330": {
    "stock_id": "2330",
    "name": "台積電",
    "open": 1070.0,
    "high": 1085.0,
    "low": 1068.0,
    "close": 1080.0,
    "change": 5.0,
    "change_percent": 0.47,
    "volume": 12345678
  }
}
```

### 3. 三大法人 (`/twse/institutional`)

```json
{
  "2330": {
    "stock_id": "2330",
    "name": "台積電",
    "foreign_net": 2345,
    "trust_net": 300,
    "dealer_net": 100,
    "total_net": 2745
  }
}
```

### 4. 即時報價 (`/twse/realtime?stock_ids=2330,2454`)

```json
{
  "2330": {
    "stock_id": "2330",
    "name": "台積電",
    "price": 1080.0,
    "change": 5.0,
    "change_percent": 0.47,
    "volume": 12345,
    "time": "13:30:00"
  }
}
```

---

## 🔧 技術細節

### 新增檔案

- `stockbuddy-backend/app/services/twse_openapi.py` - TWSE OpenAPI 服務

### 修改檔案

- `stockbuddy-backend/app/routers/stocks.py` - 新增 8 個 API 端點

### Rate Limit

- TWSE 有頻率限制：每 5 秒最多 3 個請求
- 系統已內建自動等待機制

### 快取時間

| 資料類型 | 快取時間 |
|----------|----------|
| 即時報價 | 15 秒 |
| 每日成交 | 1 分鐘 |
| 大盤指數 | 1 分鐘 |
| 本益比/殖利率 | 5 分鐘 |
| 三大法人 | 5 分鐘 |
| 融資融券 | 5 分鐘 |

---

## 🚀 使用方式

### 1. 更新後端

將 `twse_openapi.py` 複製到 `stockbuddy-backend/app/services/` 資料夾

### 2. 啟動後端

```bash
cd stockbuddy-backend
uvicorn app.main:app --reload --port 8000
```

### 3. 測試 API

開啟瀏覽器訪問：
- http://localhost:8000/api/stocks/twse/per-dividend
- http://localhost:8000/api/stocks/twse/daily-trading
- http://localhost:8000/api/stocks/twse/realtime?stock_ids=2330,2454

### 4. 查看 API 文件

http://localhost:8000/docs

---

## ⚠️ 注意事項

1. **雲端伺服器限制**：TWSE 可能會封鎖雲端伺服器 IP，在本地電腦應可正常運作
2. **交易時間**：部分 API 只在交易時段有資料
3. **週末/假日**：非交易日可能無法取得當日資料
4. **SSL 問題**：已設定 `verify=False` 處理憑證問題

---

## 📋 資料源優先順序（更新後）

| 順序 | 資料源 | 用途 | 狀態 |
|------|--------|------|------|
| 1 | **TWSE OpenAPI** | 本益比、殖利率、每日成交 | 🆕 新增 |
| 2 | **TWSE 即時** | 即時報價 | 🆕 新增 |
| 3 | FinMind | 三大法人、融資融券 | ✅ 維持 |
| 4 | yfinance | 歷史資料、基本面 | ✅ 維持 |

---

## 🔗 相關連結

- TWSE OpenAPI 官網：https://openapi.twse.com.tw/
- Swagger 文件：https://openapi.twse.com.tw/v1/swagger.json

---

*V10.7 更新完成 - 2024/12/21*
