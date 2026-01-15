# StockBuddy 股票分析程式 Skill

股票分析與投資決策輔助系統。當用戶提到「股票分析」、「StockBuddy」、「投資建議」、「股票預測」、「ML模型訓練」時使用此 skill。

## 專案資訊

| 項目 | 值 |
|------|-----|
| 專案名稱 | StockBuddy (股票分析程式) |
| 版本 | V10.41 |
| 專案路徑 | `J:\程式碼練習\股票分析程式-Claude-Code版` |
| GitHub | `https://github.com/langlive04-crypto/stockbuddy.git` |

## 技術棧

| 層級 | 技術 |
|------|------|
| 前端 | React 18 + Vite + TailwindCSS |
| 後端 | FastAPI + Python 3.12 |
| ML | XGBoost, scikit-learn |
| 資料庫 | SQLite (本地) |
| 部署 | Vercel (前端) / Railway (後端) |

## 目錄結構

```
股票分析程式-Claude-Code版/
├── stockbuddy-frontend/      # 前端專案
│   ├── src/                  # React 源碼
│   ├── dist/                 # 編譯輸出
│   ├── vercel.json           # Vercel 部署配置
│   └── vite.config.js        # Vite 配置
├── stockbuddy-backend/       # 後端專案
│   ├── app/                  # FastAPI 應用
│   │   ├── main.py           # 入口
│   │   ├── routes/           # API 路由
│   │   └── services/         # 服務層
│   ├── railway.json          # Railway 部署配置
│   ├── Procfile              # Heroku 備用
│   └── .env.example          # 環境變數範本
├── scripts/                  # 工具腳本
├── docs/                     # 文件
├── 開發日誌.md               # 開發記錄
└── 開啟Claude.bat            # 一鍵啟動
```

## 部署配置檔案 (必須版本控制)

| 檔案 | 位置 | 用途 |
|------|------|------|
| `vercel.json` | stockbuddy-frontend/ | Vercel 前端部署配置 |
| `railway.json` | stockbuddy-backend/ | Railway 後端部署配置 |
| `Procfile` | stockbuddy-backend/ | Heroku 啟動命令 |
| `.env.example` | stockbuddy-backend/ | 環境變數範本 |

## 環境變數

### 後端必要變數

```bash
# FinMind API (必須)
FINMIND_TOKEN=your_token

# JWT 設定 (必須)
JWT_SECRET_KEY=your-secure-secret-key
JWT_EXPIRE_MINUTES=1440

# CORS 設定
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# 可選
LOG_LEVEL=INFO
CACHE_TTL=300
SENTRY_DSN=
```

### 前端環境變數

```bash
# .env.production
VITE_API_URL=https://your-backend-url.railway.app
```

## Git 工作流程

### 部署前檢查清單

```bash
# 1. 確認部署配置已提交
git status
# 確認以下檔案已 staged:
#   - stockbuddy-frontend/vercel.json
#   - stockbuddy-backend/railway.json
#   - stockbuddy-backend/Procfile

# 2. 確認 .env.example 已更新
git diff stockbuddy-backend/.env.example

# 3. 建立版本標籤 (重要!)
git tag -a v10.41 -m "V10.41 增量學習系統"
git push origin v10.41
```

### 版本回滾

```bash
# 查看所有標籤
git tag -l

# 回滾到特定版本
git checkout v10.40

# 或創建回滾分支
git checkout -b rollback-to-v10.40 v10.40
```

## 常見錯誤預防

### 1. 部署配置未 commit

**問題**: 修改 vercel.json/railway.json 後忘記 commit

**預防**:
```bash
# 每次修改配置後立即
git add stockbuddy-*/vercel.json stockbuddy-*/railway.json
git commit -m "chore: update deployment config"
```

### 2. 環境變數未設定

**問題**: 新增環境變數但未在部署平台設定

**預防**:
1. 更新 `.env.example`
2. 在 Vercel/Railway 控制台新增變數
3. 記錄在開發日誌

### 3. 版本未標記

**問題**: 無法回滾到穩定版本

**預防**:
```bash
# 每次重大更新後
git tag -a vX.XX -m "版本說明"
git push origin vX.XX
```

### 4. 前後端不同步

**問題**: 前端 API 調用與後端不匹配

**預防**:
```bash
# 同時編譯並測試
cd stockbuddy-frontend && npm run build
cd ../stockbuddy-backend && uvicorn app.main:app --reload
```

## 啟動指令

### 本地開發

```bash
# 前端
cd stockbuddy-frontend
npm install
npm run dev  # http://localhost:5173

# 後端
cd stockbuddy-backend
pip install -r requirements.txt
uvicorn app.main:app --reload  # http://localhost:8000
```

### 編譯部署

```bash
# 前端編譯
cd stockbuddy-frontend
npm run build

# 後端無需編譯，直接部署
```

## API 端點 (部分)

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/stocks/{symbol}` | GET | 取得股票資料 |
| `/api/stocks/analyze/{symbol}` | GET | 股票分析 |
| `/api/stocks/ml/predict/{symbol}` | GET | ML 預測 |
| `/api/stocks/ml/train` | POST | 訓練模型 |
| `/api/market-index` | GET | 大盤指數 |
| `/api/data-status` | GET | 資料狀態 |

## 開發紀錄

- **V10.41**: 增量學習系統 (XGBoost 經驗回放)
- **V10.40**: ML 訓練器完善 (55 特徵)
- **V10.39**: 選單優化 (8 主選單)
- **V10.38**: 核心功能修正 (產業熱度動態化)

## 相關檔案

- `開發日誌.md` - 詳細開發記錄
- `docs/` - 設計文檔
- `scripts/train_ml_model.py` - ML 模型訓練

---
*最後更新: 2026-01-15*
