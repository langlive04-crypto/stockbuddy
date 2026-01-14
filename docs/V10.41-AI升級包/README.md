# StockBuddy V10.41 AI 升級包

> AI 戰略升級：SHAP + FinBERT + TFT + 強化學習

---

## 快速開始

### 1. 安裝依賴

```bash
cd stockbuddy-backend
pip install -r ../V10.41-AI升級包/requirements-v10.41.txt
```

### 2. 複製程式碼

```bash
# 後端程式碼
cp V10.41-AI升級包/後端程式碼/*.py stockbuddy-backend/app/services/

# 前端元件
cp V10.41-AI升級包/前端程式碼/*.jsx stockbuddy-frontend/src/components/
```

### 3. 執行測試

```bash
cd stockbuddy-backend
python -m pytest ../V10.41-AI升級包/測試腳本/test_phase1.py -v
```

---

## 升級包內容

```
V10.41-AI升級包/
├── README.md                    ← 本文件 (快速開始指南)
├── V10.41-升級規格書.md          ← 完整規格 (技術細節)
├── AI戰略報告.md                 ← 戰略分析 (背景說明)
├── requirements-v10.41.txt      ← Python 依賴
│
├── 後端程式碼/
│   ├── shap_explainer.py        ← SHAP 解釋性模組
│   ├── finbert_sentiment.py     ← FinBERT 情緒分析
│   ├── tft_predictor.py         ← TFT 時間序列預測
│   └── rl_agent.py              ← PPO 強化學習代理
│
├── 前端程式碼/
│   ├── SHAPWaterfall.jsx        ← SHAP 瀑布圖元件
│   └── PredictionExplainer.jsx  ← 預測解釋面板
│
└── 測試腳本/
    ├── test_phase1.py           ← Phase 1 測試 (SHAP + FinBERT)
    ├── test_phase2.py           ← Phase 2 測試 (TFT)
    └── test_phase3.py           ← Phase 3 測試 (RL)
```

---

## 實施階段

| 階段 | 內容 | 預計時間 | 驗收標準 |
|------|------|----------|----------|
| **Phase 1** | SHAP + FinBERT | 1-2 週 | test_phase1.py 全部通過 |
| **Phase 2** | TFT 時間序列 | 2-4 週 | test_phase2.py 全部通過 |
| **Phase 3** | PPO 強化學習 | 4-6 週 | test_phase3.py 全部通過 |

---

## 依賴說明

### 必要依賴

| 套件 | 版本 | 用途 |
|------|------|------|
| shap | >=0.44.0 | 模型解釋性 |
| transformers | >=4.36.0 | FinBERT 模型 |
| torch | >=2.1.0 | PyTorch 深度學習 |
| pytorch-forecasting | >=1.0.0 | TFT 預測 |
| pytorch-lightning | >=2.1.0 | 訓練框架 |
| stable-baselines3 | >=2.2.0 | PPO 強化學習 |
| gymnasium | >=0.29.0 | RL 環境 |

### 硬體建議

- **Phase 1**: CPU 即可
- **Phase 2-3**: GPU 建議 (NVIDIA RTX 3060+ 或同等級)

---

## 整合步驟

### Phase 1: SHAP + FinBERT

1. **安裝依賴**
   ```bash
   pip install shap>=0.44.0 transformers>=4.36.0 torch>=2.1.0
   ```

2. **複製檔案**
   ```bash
   cp 後端程式碼/shap_explainer.py stockbuddy-backend/app/services/
   cp 後端程式碼/finbert_sentiment.py stockbuddy-backend/app/services/
   ```

3. **修改 ml_predictor.py**
   ```python
   from app.services.shap_explainer import explain_prediction

   # 在 predict 方法中加入解釋
   explanation = explain_prediction(self._model, feature_names, features, stock_id)
   ```

4. **修改 news_service.py**
   ```python
   from app.services.finbert_sentiment import analyze_sentiment

   # 替換關鍵字情緒分析
   sentiment = analyze_sentiment(news_text, language="zh")
   ```

5. **新增 API 路由** (ml_routes.py)
   ```python
   @router.get("/explain/{stock_id}")
   async def explain_prediction_api(stock_id: str):
       # 呼叫 SHAP 解釋
       return explain_prediction(...)
   ```

6. **執行測試**
   ```bash
   python -m pytest ../V10.41-AI升級包/測試腳本/test_phase1.py -v
   ```

---

## 驗收清單

### Phase 1 驗收項目

- [ ] SHAP 套件成功安裝
- [ ] shap_explainer.py 可正常導入
- [ ] explain_prediction() 回傳正確格式
- [ ] FinBERT 模型成功下載
- [ ] 中文情緒分析準確率 > 75%
- [ ] API /explain/{stock_id} 正常回應
- [ ] 前端 SHAP 瀑布圖正常顯示

### Phase 2 驗收項目

- [ ] TFT 模型訓練完成
- [ ] 預測準確率 > XGBoost 基準
- [ ] 注意力權重可視覺化

### Phase 3 驗收項目

- [ ] RL 環境正常運行
- [ ] PPO 代理訓練收斂
- [ ] 交易建議 API 正常

---

## 常見問題

### Q: FinBERT 模型下載很慢？

首次使用會從 HuggingFace 下載模型 (~440MB)，請確保網路連線。

```python
# 可預先下載
from transformers import AutoTokenizer, AutoModel
AutoTokenizer.from_pretrained("ProsusAI/finbert")
AutoModel.from_pretrained("ProsusAI/finbert")
```

### Q: CUDA 記憶體不足？

TFT 和 RL 訓練建議至少 8GB GPU 記憶體。可調整：

```python
# tft_predictor.py
batch_size = 16  # 降低批次大小
```

### Q: 沒有 GPU 可以跑嗎？

- Phase 1 (SHAP + FinBERT): CPU 可運行
- Phase 2-3: CPU 可運行但速度較慢

---

## 聯絡資訊

如有問題，請聯繫開發團隊。

---

*V10.41 升級包 - 2026-01-15*
