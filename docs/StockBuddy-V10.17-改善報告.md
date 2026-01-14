# StockBuddy V10.17 改善報告與開發計劃

> **建立日期**：2026/01/09
> **更新時間**：2026/01/10
> **當前版本**：V10.17
> **開發者**：Claude Code (Claude Opus 4.5)

---

## 一、用戶回報問題清單

### 1.1 問題總覽

| 編號 | 問題描述 | 優先級 | 狀態 |
|------|----------|--------|------|
| P-01 | AI精選日期顯示錯誤 | 🔴 高 | ✅ 已完成 |
| P-02 | AI精選個股績效呈現雜亂 | 🔴 高 | ✅ 已完成 |
| P-03 | 綜合策略版面需優化 | 🔴 高 | ✅ 已完成 |
| P-04 | 選股篩選只顯示代號 | 🟡 中 | ✅ 已完成 |
| P-05 | 需持續新增功能與改善AI | 🟢 低 | ⏳ 進行中 |

---

## 二、問題詳細分析與解決方案

### 2.1 P-01: AI精選日期顯示錯誤

**問題描述**：
- 當前日期顯示的是資料獲取日期（如1/8）
- 用戶期望顯示當前日期（如1/9），並標示資料是舊資料

**現有程式碼位置**：
- `stockbuddy-frontend/src/App.jsx` 第2847-2862行

**解決方案**：
1. 修改日期顯示邏輯，顯示當前日期
2. 如果資料日期早於今天，添加「(舊資料)」標示
3. 在獲取資料時，嘗試尋找最新資料，若無則使用舊資料

**狀態**：✅ 已完成

**修改內容**：
- 修改 `App.jsx` 第2847-2867行
- 現在顯示當前日期（如 1/9）
- 若資料是舊資料，會顯示「2026/01/08 舊資料 ⚠️」標籤（黃色）
- 若為最新資料則顯示綠色日期

**程式碼變更**：
```javascript
{(() => {
  const today = new Date();
  const todayStr = `${today.getFullYear()}/${String(today.getMonth() + 1).padStart(2, '0')}/${String(today.getDate()).padStart(2, '0')}`;
  const displayDate = `${today.getMonth() + 1}/${today.getDate()}`;
  const isOldData = dataDate && dataDate !== todayStr;
  return (
    <span className={isOldData ? 'text-yellow-400' : 'text-emerald-400'}>
      📅 {displayDate}
      {isOldData && (
        <span className="ml-1 px-1.5 py-0.5 bg-yellow-500/20 rounded text-xs">
          {dataDate} 舊資料 ⚠️
        </span>
      )}
    </span>
  );
})()}
```

---

### 2.2 P-02: AI精選個股績效呈現雜亂

**問題描述**：
- 多維度分數（技/基/籌/聞）顯示過於擁擠
- 專有名詞對客戶來說太深奧
- 缺乏詳細報告或介紹

**現有程式碼位置**：
- `stockbuddy-frontend/src/App.jsx` 第415-551行 (StockCard組件)

**解決方案**：
1. 重新設計 StockCard 版面，更整潔直觀
2. 增加「說明」tooltip，解釋專有名詞
3. 增加「詳細分析」展開區域
4. 使用更直觀的視覺化（如進度條、評級星星）

**改進項目**：
- [x] 重新排版多維度分數，使用圖形化呈現（進度條）
- [x] 添加專有名詞解釋 tooltip（TermTooltip 組件）
- [x] 增加投資建議說明（白話文版本）
- [x] 優化交易建議區（止損/目標價位卡片）
- [x] 改善追蹤按鈕視覺效果

**狀態**：✅ 已完成

**修改內容**：
- 新增 `TermTooltip` 組件：滑鼠懸停時顯示專有名詞解釋
- 新增 `ScoreBar` 組件：以進度條視覺化呈現各維度評分
- 重新設計 `StockCard` 組件版面：
  - 四維評分改用進度條呈現，更直覺
  - 新增白話文建議功能 `getSimpleAdvice()`
  - 交易建議改為卡片式呈現
  - 追蹤按鈕使用漸層色彩

**新增組件**：
```javascript
// TermTooltip - 專有名詞解釋 tooltip
const TermTooltip = ({ term, children }) => {
  const termExplanations = {
    '技術面': '根據股價走勢和成交量分析，判斷買賣時機',
    '基本面': '分析公司財務狀況，評估股票是否值得投資',
    '籌碼面': '追蹤大戶和法人的買賣動向',
    '新聞面': '根據新聞消息評估對股價的影響',
    // ... 更多解釋
  };
  // ... 實作
};

// ScoreBar - 進度條視覺化評分
const ScoreBar = ({ label, score, maxScore = 100, color = 'blue' }) => {
  const percentage = Math.min((score / maxScore) * 100, 100);
  // ... 進度條呈現
};
```

---

### 2.3 P-03: 綜合策略版面需優化

**問題描述**：
- 版面呈現可參考AI精選的方式
- 點選個股時需要顯示詳細分析
- 預算規劃需列出配置方案的%數和金額

**現有程式碼位置**：
- `stockbuddy-frontend/src/components/StrategyPicksPanel.jsx`

**狀態**：✅ 已完成

**修改內容**：

#### 3.1 新增 StockDetailPanel 組件
點選個股時展開詳細分析面板，包含：
- 四維度評分（技術/基本/籌碼/新聞）進度條
- 評級原因說明
- 交易策略建議（止損/目標價）
- 白話文投資建議

#### 3.2 增強 BudgetPlanner 組件
預算規劃現在顯示完整配置明細：
```
預算: 100,000 NT$ | 風險等級: 穩健

配置方案：
┌─────────┬────────┬──────────┬──────────┬────────┬──────────┐
│ 股票    │ 權重   │ 配置金額 │ 參考股價 │ 建議張數│ 實際金額 │
├─────────┼────────┼──────────┼──────────┼────────┼──────────┤
│ 台積電  │ 25%    │ 25,000元 │ 1095元   │ 0.02張 │ 21,900元 │
│ 聯發科  │ 20%    │ 20,000元 │ 580元    │ 0.03張 │ 17,400元 │
│ ...     │ ...    │ ...      │ ...      │ ...    │ ...      │
└─────────┴────────┴──────────┴──────────┴────────┴──────────┘
```

**程式碼變更**：
- 新增 `ScoreProgressBar` 組件
- 新增 `StockDetailPanel` 組件
- 重構 `BudgetPlanner` 組件，增加配置明細表格

---

### 2.4 P-04: 選股篩選只顯示代號

**問題描述**：
- 個股僅以數字代號呈現
- 應該有中文名稱及代號並列

**現有程式碼位置**：
- 前端：`stockbuddy-frontend/src/components/StockScreener.jsx` 第27-98行
- 後端：`stockbuddy-backend/app/services/stock_screener.py`

**狀態**：✅ 已完成

**修改內容**：

#### 前端修改 (StockScreener.jsx)
```javascript
// 修改前
<div className="text-white font-semibold">
  {stock.stock_id}
</div>

// 修改後
const stockName = stock.name || stock.stock_name || stock.stock_id;
<div className="text-white font-semibold">
  {stockName} <span className="text-slate-500">({stock.stock_id})</span>
</div>
```

#### 後端修改 (stock_screener.py)
```python
# 在返回的股票資料中加入名稱
from app.services.stock_data import get_stock_name

matched_stocks.append({
    "stock_id": stock_id,
    "name": get_stock_name(stock_id),       # V10.17 新增
    "stock_name": get_stock_name(stock_id), # V10.17 新增 (相容性)
    # ... 其他欄位
})
```

---

## 三、新功能規劃與已實作項目

### 3.1 V10.17 新增技術指標（後端已完成）

| 指標 | 說明 | 後端狀態 | 前端狀態 |
|------|------|----------|----------|
| KD 指標 | 隨機指標，判斷超買超賣 | ✅ 已完成 | ⏳ 待新增 |
| 威廉指標 (Williams %R) | 動量指標，-100到0範圍 | ✅ 已完成 | ⏳ 待新增 |
| 風險評估 | 根據波動性評估投資風險 | ✅ 已完成 | ⏳ 待新增 |

**後端程式碼位置**：
- `stockbuddy-backend/app/services/technical_analysis.py`

**新增函數**：
```python
# KD 指標計算
@staticmethod
def calculate_kd(highs, lows, closes, period=9):
    # 計算 K 值和 D 值

# 威廉指標計算
@staticmethod
def calculate_williams_r(highs, lows, closes, period=14):
    # 計算威廉指標 (-100 到 0)

# 風險評估
@staticmethod
def calculate_risk_score(closes, volumes):
    # 根據波動性計算風險分數
```

### 3.2 近期新增項目

| 功能 | 說明 | 優先級 | 狀態 |
|------|------|--------|------|
| 自動資料更新 | 定時自動更新最新資料 | 🔴 高 | ⏳ 規劃中 |
| 歷史績效追蹤 | 追蹤推薦股票後續表現 | 🔴 高 | ⏳ 規劃中 |
| 個股對比工具 | 多檔股票並排比較 | 🟡 中 | ✅ 已完成 |
| 價格警示通知 | 目標價/止損價提醒 | 🟡 中 | ✅ 已完成 |

### 3.3 AI分析能力提升計劃

| 改進項目 | 說明 | 狀態 |
|----------|------|------|
| 新聞情緒分析增強 | 加入更多新聞來源，提高準確度 | ⏳ 規劃中 |
| 技術面指標擴充 | 增加KD、威廉指標等 | ✅ V10.17 後端完成 |
| 產業連動分析 | 分析產業鏈上下游關聯 | ⏳ 規劃中 |
| 法人買賣預測 | 預測法人未來動向 | ⏳ 規劃中 |
| 季報/年報分析 | 自動解讀財報重點 | ⏳ 規劃中 |
| 智能風險評估 | 根據波動性和基本面評估投資風險 | ✅ V10.17 後端完成 |
| 相似股票推薦 | 根據產業和特性推薦類似股票 | ✅ V10.17 新增 |
| 市場情緒指標 | 綜合多項指標評估市場整體情緒 | ✅ V10.17 新增 |

### 3.4 用戶體驗改善

| 改進項目 | 說明 | 狀態 |
|----------|------|------|
| 白話文解說 | 所有專有名詞附帶白話文解釋 | ✅ 已完成 (TermTooltip) |
| 新手引導 | 首次使用引導教學 | ⏳ 規劃中 |
| 黑暗/淺色主題 | 主題切換功能 | ⏳ 規劃中 |
| 手機版優化 | RWD響應式設計改善 | ⏳ 規劃中 |

---

## 四、開發進度追蹤

### 2026/01/09 - 2026/01/10 開發任務

| 任務 | 狀態 | 修改檔案 |
|------|------|----------|
| 建立改善報告與清單 | ✅ 已完成 | `docs/StockBuddy-V10.17-改善報告.md` |
| 修正AI精選日期顯示 | ✅ 已完成 | `App.jsx` 第2847-2867行 |
| 優化AI精選個股績效呈現 | ✅ 已完成 | `App.jsx` (TermTooltip, ScoreBar, StockCard) |
| 優化綜合策略版面 | ✅ 已完成 | `StrategyPicksPanel.jsx` |
| 修正選股篩選顯示 | ✅ 已完成 | `StockScreener.jsx`, `stock_screener.py` |
| 新增技術指標 (後端) | ✅ 已完成 | `technical_analysis.py` |
| 新增技術指標 (前端) | ⏳ 進行中 | `App.jsx` (AnalysisPanel) |

---

## 五、修改檔案清單

### 前端 (stockbuddy-frontend)

| 檔案 | 修改內容 |
|------|----------|
| `src/App.jsx` | 日期顯示、TermTooltip、ScoreBar、StockCard 重構 |
| `src/components/StrategyPicksPanel.jsx` | StockDetailPanel、BudgetPlanner 增強 |
| `src/components/StockScreener.jsx` | 股票名稱顯示修正 |

### 後端 (stockbuddy-backend)

| 檔案 | 修改內容 |
|------|----------|
| `app/services/stock_screener.py` | 返回資料加入股票名稱 |
| `app/services/technical_analysis.py` | 新增 KD、威廉指標、風險評估 |

---

## 六、版本歷史

| 版本 | 日期 | 更新內容 |
|------|------|----------|
| V10.17 | 01/09-01/10 | 日期顯示修正、版面優化、名稱顯示修正、新增技術指標 |
| V10.16 | 01/09 | 綜合投資策略系統、專業投顧評級 |
| V10.15 | 01/09 | 績效分析、K線圖、匯出功能、上櫃股票 |
| V10.14.2 | 01/07 | 並發控制、漲跌幅修正 |

---

## 七、技術債清單

| 項目 | 說明 | 優先級 |
|------|------|--------|
| App.jsx 過大 | 約120KB，應拆分為多個組件 | 🟡 中 |
| stocks.py 過大 | 約93KB，應拆分路由 | 🟡 中 |
| 測試覆蓋不足 | 缺少單元測試和集成測試 | 🟢 低 |
| 日誌系統不完善 | 缺少結構化日誌 | 🟢 低 |

---

## 八、待完成項目

### 立即待辦
1. [ ] 前端新增 KD、威廉指標、風險評估顯示
2. [ ] 更新 AnalysisPanel 技術面分頁

### 短期規劃
1. [ ] 自動資料更新功能
2. [ ] 歷史績效追蹤系統
3. [ ] 新手引導功能

---

*最後更新：2026/01/10*
*開發者：Claude Code (Claude Opus 4.5)*
