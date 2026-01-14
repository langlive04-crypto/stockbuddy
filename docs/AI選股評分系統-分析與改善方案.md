# AI 選股評分系統 - 分析與改善方案

> 建立日期：2026-01-12
> 版本：V1.0
> 狀態：待實作

---

## 目錄

1. [問題背景](#問題背景)
2. [現有評分系統分析](#現有評分系統分析)
3. [問題一：每日換股現象](#問題一每日換股現象)
4. [問題二：評分選股是否為賭博](#問題二評分選股是否為賭博)
5. [問題三：兩套評分系統差異](#問題三兩套評分系統差異)
6. [問題四：多種評分標準的價值](#問題四多種評分標準的價值)
7. [改善方案總覽](#改善方案總覽)
8. [實作計畫](#實作計畫)

---

## 問題背景

專案管理人提出以下觀察與疑問：

1. AI 精選勝率雖高，但每日換股劇烈（今天 10 檔，隔天可能全換）
2. 評分選股是否實質上只是賭博？
3. AI 精選分數與個股詳情策略分數不一致，哪種好？
4. 多種評分標準是好是壞？

---

## 現有評分系統分析

### 系統總覽

| 維度 | AI 精選系統 | 個股詳情系統 |
|------|-------------|--------------|
| **檔案位置** | `ai_stock_picker.py` | `scoring_service.py` + `investment_strategy.py` |
| **API 端點** | `/api/stocks/ai-picks` | `/api/stocks/strategy/{stock_id}` |
| **用途** | 全市場篩選 Top 10 | 單檔深度分析 |
| **版本** | V10.7.1 | V10.10-V10.16 |

### 權重配置對比

```
AI 精選系統：
┌─────────────────────────────────────────┐
│  技術面 40%  │  籌碼面 35%  │  基本面 25%  │
└─────────────────────────────────────────┘
+ 日漲幅獎勵 (+2~8 分)

個股詳情系統：
┌──────────────────────────────────────────────────┐
│  技術面 30%  │  籌碼面 30%  │  基本面 25%  │  產業 15%  │
└──────────────────────────────────────────────────┘
+ 融資融券加分 + 新聞情緒
```

### 評分範圍

| 系統 | 最低分 | 最高分 |
|------|--------|--------|
| AI 精選 | 15 | 95 |
| 個股詳情 | 10 | 95 |

---

## 問題一：每日換股現象

### 現象描述

> 今天出現的十檔，隔天卻一檔不留或只剩幾檔，就像換了一批

### 根本原因分析

| 原因 | 說明 | 影響程度 |
|------|------|----------|
| **日漲幅獎勵機制** | 當日漲幅 >5% 直接加 8 分，隔天歸零 | ⭐⭐⭐⭐⭐ 主因 |
| **技術面權重 40%** | RSI、MACD 等短期指標變化快 | ⭐⭐⭐⭐ |
| **籌碼面權重 35%** | 三大法人買賣超每日變動大 | ⭐⭐⭐⭐ |
| **無「持續性」指標** | 系統只看當日數據，無考慮連續表現 | ⭐⭐⭐⭐⭐ 主因 |
| **台股特性** | 散戶比例高、題材炒作快速輪動 | ⭐⭐⭐ |

### 核心問題

```
現行邏輯：誰今天漲最多、籌碼最好 → 選誰
缺少邏輯：誰連續表現穩定、趨勢向上 → 選誰

系統偏向「動能」而非「趨勢」
```

### 日漲幅獎勵機制詳情

```python
# 現行代碼 (ai_stock_picker.py)
if change_percent >= 5:
    score += 8   # 漲幅 >5% 加 8 分
elif change_percent >= 3:
    score += 5   # 漲幅 3-5% 加 5 分
elif change_percent >= 1:
    score += 2   # 漲幅 1-3% 加 2 分
```

**問題**：這導致「追漲」行為，今天漲停的股票容易入選，但隔天可能回檔。

---

## 問題二：評分選股是否為賭博

### 賭博 vs 投資 特徵對比

| 特徵 | 賭博 | 投資 | 我們系統 |
|------|------|------|----------|
| 結果不確定 | ✅ | ✅ | ✅ |
| 有風險 | ✅ | ✅ | ✅ |
| 追求報酬 | ✅ | ✅ | ✅ |
| 基於數據分析 | ❌ | ✅ | ✅ |
| 有邏輯依據 | ❌ | ✅ | ✅ |
| 風險可控 | ❌ | ✅ | ⚠️ 部分 |
| **歷史驗證** | ❌ | ✅ | ❌ 缺少 |
| **績效追蹤** | ❌ | ✅ | ❌ 缺少 |

### 結論

**現況：「有依據的投機」而非純賭博**

我們系統具備：
- ✅ 有邏輯依據：技術面、基本面、籌碼面、產業熱度
- ✅ 數據驅動：三大法人、P/E、RSI 等客觀數據
- ✅ 風險提示：有風險評估、止損建議

但缺少：
- ❌ 回測驗證：無法證明歷史勝率
- ❌ 持續追蹤：選出後無追蹤表現
- ❌ 勝率統計：用戶無法判斷系統可靠性

---

## 問題三：兩套評分系統差異

### 詳細權重對比

#### 技術面評分

| 指標 | AI 精選 (40%) | 個股詳情 (30%) |
|------|---------------|----------------|
| 均線分析 | 25 分 | 25 分 |
| RSI | 20 分 | 15 分 |
| MACD | 20 分 | 15 分 |
| KD | 15 分 | 10 分 |
| 成交量 | 15 分 | 10 分 |
| 布林通道 | 無 | 5 分 |

#### 籌碼面評分

| 指標 | AI 精選 (35%) | 個股詳情 (30%) |
|------|---------------|----------------|
| 外資買賣超 | 15 分 | 18 分 |
| 投信買賣超 | 10 分 | 10 分 |
| 自營商 | 5 分 | 4 分 |
| 三大法人合計 | 20 分 | 無 |
| 融資融券 | 10 分 | 10 分 (V10.11) |

#### 基本面評分

| 指標 | AI 精選 (25%) | 個股詳情 (25%) |
|------|---------------|----------------|
| P/E | 30 分 | 25 分 |
| 殖利率 | 20 分 | 20 分 |
| P/B | 10 分 | 10 分 |
| 營收 YoY | 20 分 | 無 |

#### 產業熱度 (個股詳情獨有 15%)

```
熱門題材 (+8~+12)：AI、HBM、CoWoS、先進製程
熱門產業 (+4~+6)：半導體、IC設計、電動車
中性 (0)：金控、銀行、電信
冷門 (-3~-5)：塑膠、石化、紡織
```

### 分數差異示例

以台積電 (2330) 為例：

```
AI 精選計算：
  技術 85 × 40% = 34
  籌碼 70 × 35% = 24.5
  基本 60 × 25% = 15
  ─────────────────
  總分 = 73.5 分

個股詳情計算：
  技術 80 × 30% = 24
  籌碼 70 × 30% = 21
  基本 65 × 25% = 16.25
  產業 90 × 15% = 13.5
  ─────────────────
  總分 = 74.75 分
```

### 適用場景

| 場景 | 推薦系統 | 原因 |
|------|----------|------|
| 短線交易 | AI 精選 | 技術 40%、籌碼 35%，動能導向 |
| 中長線投資 | 個股詳情 | 產業 15%、基本面完整 |
| 價值投資 | 個股詳情 | P/E、殖利率分析更細緻 |
| 快速篩選 | AI 精選 | Top 10 一目瞭然 |
| 深度分析 | 個股詳情 | 有交易策略、風險評估 |

---

## 問題四：多種評分標準的價值

### 優缺點分析

| 優點 | 缺點 |
|------|------|
| ✅ 多角度分析，更全面 | ❌ 用戶困惑：該看哪個分數？ |
| ✅ 不同投資風格可參考不同指標 | ❌ 分數不一致降低信任度 |
| ✅ 專業用戶可自行判斷 | ❌ 新手用戶無所適從 |
| ✅ 展現系統專業度 | ❌ 維護成本較高 |

### 結論

**多種評分標準是好事，但需要清楚標示用途**

---

## 改善方案總覽

### 方案 A：連續性加分機制

**目的**：解決每日換股問題

**實作內容**：
```python
# 新增連續性評分
continuity_score = 0

# 連續外資買超
if foreign_buy_days >= 3:
    continuity_score += 5
if foreign_buy_days >= 5:
    continuity_score += 3  # 額外加分

# 連續站穩均線
if days_above_ma5 >= 5:
    continuity_score += 5

# 連續成交量放大
if volume_increase_days >= 3:
    continuity_score += 3

# 上週曾入選 AI 精選
if was_in_ai_picks_last_week:
    continuity_score += 3  # 持續追蹤獎勵
```

**影響檔案**：
- `ai_stock_picker.py`

**複雜度**：中

---

### 方案 B：降低日漲幅權重

**目的**：減少追漲行為

**實作內容**：
```python
# 現行
if change_percent >= 5:
    score += 8

# 改為
if change_percent >= 5:
    score += 3  # 從 +8 降為 +3
elif change_percent >= 3:
    score += 2  # 從 +5 降為 +2
elif change_percent >= 1:
    score += 1  # 從 +2 降為 +1
```

**影響檔案**：
- `ai_stock_picker.py`

**複雜度**：低

---

### 方案 C：新增穩定度指標

**目的**：評估股票表現穩定性

**實作內容**：
```python
def calculate_stability_score(stock_data):
    """
    穩定度指標 (0-20 分)
    """
    score = 0

    # 連續上漲天數 (最高 8 分)
    consecutive_up_days = get_consecutive_up_days(stock_data)
    score += min(consecutive_up_days * 2, 8)

    # 連續籌碼買超天數 (最高 8 分)
    consecutive_buy_days = get_consecutive_buy_days(stock_data)
    score += min(consecutive_buy_days * 2, 8)

    # 波動率低於平均 (最高 4 分)
    if volatility < market_avg_volatility:
        score += 4

    return score
```

**權重調整**：
```
原：技術 40% + 籌碼 35% + 基本 25%
新：技術 35% + 籌碼 30% + 基本 25% + 穩定度 10%
```

**影響檔案**：
- `ai_stock_picker.py`

**複雜度**：中

---

### 方案 D：AI 精選績效追蹤

**目的**：驗證系統有效性，消除賭博疑慮

**實作內容**：

#### 後端 API
```python
# 新增 API 端點
@router.get("/ai-picks/performance")
async def get_ai_picks_performance():
    """
    回傳 AI 精選歷史績效
    """
    return {
        "summary": {
            "total_picks": 500,        # 總選股次數
            "win_rate_t1": 58.2,       # T+1 勝率
            "win_rate_t5": 62.5,       # T+5 勝率
            "win_rate_t20": 55.8,      # T+20 勝率
            "avg_return_t1": 1.2,      # T+1 平均報酬
            "avg_return_t5": 3.5,      # T+5 平均報酬
            "avg_return_t20": 5.8,     # T+20 平均報酬
            "max_drawdown": -8.5,      # 最大回撤
        },
        "recent_picks": [
            {
                "date": "2026-01-10",
                "stocks": ["2330", "2454", ...],
                "return_t1": 1.5,
                "return_t5": 3.2,
            },
            ...
        ]
    }
```

#### 資料儲存
```python
# 新增資料表或 JSON 儲存
AI_PICKS_HISTORY = {
    "2026-01-10": {
        "picks": ["2330", "2454", "2317", ...],
        "prices": {"2330": 1015, "2454": 1210, ...},
    },
    ...
}
```

#### 前端面板
```jsx
// 新增 AIPicksPerformance.jsx
<div className="bg-slate-800 rounded-lg p-4">
  <h3>AI 精選歷史績效</h3>

  <div className="grid grid-cols-3 gap-4">
    <StatCard title="T+1 勝率" value="58.2%" />
    <StatCard title="T+5 勝率" value="62.5%" />
    <StatCard title="T+20 勝率" value="55.8%" />
  </div>

  <div className="mt-4">
    <h4>近期表現</h4>
    <PerformanceChart data={recentPicks} />
  </div>
</div>
```

**影響檔案**：
- `stocks.py` (新增 API)
- 新增 `ai_picks_tracker.py`
- 新增 `AIPicksPerformance.jsx`

**複雜度**：中

---

### 方案 E：統一命名標示

**目的**：消除分數困惑

**實作內容**：

```jsx
// 現況
<span>AI 精選分數：73 分</span>
<span>投資策略分數：75 分</span>

// 改為
<span>
  <span className="text-amber-400">動能評分</span>：73 分
  <span className="text-xs text-slate-400">（適合短線）</span>
</span>

<span>
  <span className="text-blue-400">價值評分</span>：75 分
  <span className="text-xs text-slate-400">（適合中長線）</span>
</span>
```

**命名規範**：
| 原名稱 | 新名稱 | 適用場景 |
|--------|--------|----------|
| AI 精選分數 | 動能評分 | 短線、波段 |
| 投資策略分數 | 價值評分 | 中長線、價值投資 |

**影響檔案**：
- `App.jsx`
- `StrategyPicksPanel.jsx`
- `StrategyDashboard.jsx`

**複雜度**：低

---

### 方案 F：評分說明提示

**目的**：讓用戶理解評分含義

**實作內容**：

```jsx
// 新增 Tooltip 組件
<ScoreTooltip type="momentum">
  <div className="p-3 max-w-xs">
    <h4 className="font-bold mb-2">動能評分說明</h4>
    <div className="text-sm space-y-1">
      <p>技術面：40%</p>
      <p>籌碼面：35%</p>
      <p>基本面：25%</p>
    </div>
    <div className="mt-2 text-xs text-slate-400">
      偏重短期動能，適合波段操作
    </div>
  </div>
</ScoreTooltip>

<ScoreTooltip type="value">
  <div className="p-3 max-w-xs">
    <h4 className="font-bold mb-2">價值評分說明</h4>
    <div className="text-sm space-y-1">
      <p>技術面：30%</p>
      <p>籌碼面：30%</p>
      <p>基本面：25%</p>
      <p>產業熱度：15%</p>
    </div>
    <div className="mt-2 text-xs text-slate-400">
      兼顧成長與價值，適合中長線投資
    </div>
  </div>
</ScoreTooltip>
```

**影響檔案**：
- 新增 `ScoreTooltip.jsx`
- `App.jsx`
- `StrategyPicksPanel.jsx`

**複雜度**：低

---

### 方案 G：自訂權重功能

**目的**：滿足不同用戶需求

**實作內容**：

```jsx
// 新增 CustomWeightPanel.jsx
const CustomWeightPanel = () => {
  const [weights, setWeights] = useState({
    technical: 40,
    chip: 35,
    fundamental: 25,
    industry: 0,
  });

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <h3>自訂評分權重</h3>

      <div className="space-y-4">
        <WeightSlider
          label="技術面"
          value={weights.technical}
          onChange={(v) => setWeights({...weights, technical: v})}
        />
        <WeightSlider
          label="籌碼面"
          value={weights.chip}
          onChange={(v) => setWeights({...weights, chip: v})}
        />
        <WeightSlider
          label="基本面"
          value={weights.fundamental}
          onChange={(v) => setWeights({...weights, fundamental: v})}
        />
        <WeightSlider
          label="產業熱度"
          value={weights.industry}
          onChange={(v) => setWeights({...weights, industry: v})}
        />
      </div>

      <div className="mt-4 text-sm text-slate-400">
        總權重：{Object.values(weights).reduce((a, b) => a + b, 0)}%
        {Object.values(weights).reduce((a, b) => a + b, 0) !== 100 &&
          <span className="text-red-400 ml-2">（需等於 100%）</span>
        }
      </div>

      <button
        onClick={applyCustomWeights}
        className="mt-4 w-full py-2 bg-blue-600 rounded-lg"
      >
        套用自訂權重
      </button>
    </div>
  );
};
```

**後端支援**：
```python
@router.post("/ai-picks/custom")
async def get_custom_ai_picks(weights: WeightConfig):
    """
    根據自訂權重計算 AI 精選
    """
    # 驗證權重總和 = 100
    # 使用自訂權重計算
    # 回傳結果
```

**影響檔案**：
- 新增 `CustomWeightPanel.jsx`
- `stocks.py` (新增 API)
- `ai_stock_picker.py` (支援自訂權重)

**複雜度**：高

---

## 實作計畫

### 優先順序

| 順序 | 方案 | 解決問題 | 複雜度 | 預估工時 |
|------|------|----------|--------|----------|
| 1 | **E: 統一命名標示** | #3, #4 | 低 | 1 小時 |
| 2 | **F: 評分說明提示** | #3, #4 | 低 | 2 小時 |
| 3 | **B: 降低日漲幅權重** | #1 | 低 | 0.5 小時 |
| 4 | **A: 連續性加分機制** | #1 | 中 | 3 小時 |
| 5 | **C: 新增穩定度指標** | #1 | 中 | 3 小時 |
| 6 | **D: AI 精選績效追蹤** | #2 | 中 | 5 小時 |
| 7 | **G: 自訂權重功能** | #4 | 高 | 8 小時 |

### 實作檢核表

- [ ] **方案 E**：統一命名標示
  - [ ] 修改 App.jsx 中的分數顯示
  - [ ] 修改 StrategyPicksPanel.jsx
  - [ ] 修改 StrategyDashboard.jsx

- [ ] **方案 F**：評分說明提示
  - [ ] 建立 ScoreTooltip.jsx 組件
  - [ ] 整合到各分數顯示處

- [ ] **方案 B**：降低日漲幅權重
  - [ ] 修改 ai_stock_picker.py 的日漲幅加分邏輯

- [ ] **方案 A**：連續性加分機制
  - [ ] 新增連續性數據取得函數
  - [ ] 修改 ai_stock_picker.py 加入連續性評分
  - [ ] 調整權重配置

- [ ] **方案 C**：新增穩定度指標
  - [ ] 新增 calculate_stability_score 函數
  - [ ] 整合到 AI 精選評分系統
  - [ ] 調整權重配置

- [ ] **方案 D**：AI 精選績效追蹤
  - [ ] 建立歷史記錄儲存機制
  - [ ] 新增績效計算 API
  - [ ] 建立 AIPicksPerformance.jsx 面板
  - [ ] 整合到前端顯示

- [ ] **方案 G**：自訂權重功能
  - [ ] 建立 CustomWeightPanel.jsx
  - [ ] 新增後端 API 支援
  - [ ] 修改 ai_stock_picker.py 支援自訂權重

---

## 預期成效

| 改善項目 | 現況 | 目標 |
|----------|------|------|
| 每日換股率 | ~80% | <50% |
| 用戶對分數的理解度 | 低 | 高 |
| 系統可驗證性 | 無 | 有績效追蹤 |
| 用戶自訂彈性 | 無 | 可自訂權重 |

---

## 附錄：相關檔案路徑

### 後端
```
data/股票程式開發/stockbuddy-backend/app/services/
├── ai_stock_picker.py      # AI 精選系統
├── scoring_service.py      # 評分服務
├── investment_strategy.py  # 投資策略
└── technical_analysis.py   # 技術分析
```

### 前端
```
data/股票程式開發/stockbuddy-frontend/src/
├── App.jsx
└── components/
    ├── StrategyPicksPanel.jsx
    ├── StrategyDashboard.jsx
    └── (待新增) AIPicksPerformance.jsx
    └── (待新增) ScoreTooltip.jsx
    └── (待新增) CustomWeightPanel.jsx
```

---

*文件建立：2026-01-12*
*最後更新：2026-01-12*
