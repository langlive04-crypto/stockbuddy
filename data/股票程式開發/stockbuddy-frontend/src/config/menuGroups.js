/**
 * menuGroups.js - V10.40 優化版
 *
 * 選單群組定義檔
 *
 * 安裝位置: stockbuddy-frontend/src/config/menuGroups.js
 *
 * 變更說明:
 * - 29 個選單整合為 8 個主群組
 * - 績效追蹤整合 (tracker + history-perf)
 * - 提醒通知整合 (alerts + smart-alerts)
 * - 投資日記移入投組群組
 * - 模擬交易移入策略群組
 * - V10.40: 新增 ML 模型管理
 */

/**
 * 選單群組結構 - 8 個主選單
 */
export const menuGroups = [
  {
    id: 'market',
    label: '📊 市場',
    defaultSection: 'dashboard',
    items: [
      { id: 'dashboard', label: '市場總覽', icon: '📊', desc: '台美股市場即時概況' },
      { id: 'calendar', label: '行事曆', icon: '📅', desc: '除權息、休市日、重要事件' },
      { id: 'news', label: '財經新聞', icon: '📰', desc: '即時新聞與情緒分析' },
    ]
  },
  {
    id: 'ai-pick',
    label: '🎯 AI選股',
    defaultSection: 'ai',
    items: [
      { id: 'ai', label: 'AI 精選', icon: '🎯', desc: '依技術分析評分排序' },
      { id: 'hot', label: '熱門飆股', icon: '🔥', desc: '當日漲幅最大' },
      { id: 'volume', label: '成交熱門', icon: '📊', desc: '成交量比率最高' },
      { id: 'dark', label: '潛力黑馬', icon: '🐴', desc: '評分中等但有上漲潛力' },
      { id: 'screener', label: '進階篩選', icon: '🔍', desc: '多條件自訂篩選' },
    ]
  },
  {
    id: 'analysis',
    label: '🔍 分析',
    defaultSection: 'search',
    items: [
      { id: 'search', label: '個股查詢', icon: '🔎', desc: '查詢任意股票AI分析' },
      { id: 'compare', label: '多股比較', icon: '⚖️', desc: '並排比較多檔股票' },
      { id: 'ai-report', label: 'AI 報告', icon: '📝', desc: '個股深度分析報告' },
      { id: 'patterns', label: '形態辨識', icon: '🔍', desc: '技術形態自動辨識' },
      { id: 'adv-charts', label: '進階圖表', icon: '📈', desc: '技術/籌碼/產業分析' },
    ]
  },
  {
    id: 'strategy',
    label: '📋 策略',
    defaultSection: 'strategy',
    items: [
      { id: 'strategy', label: '綜合策略', icon: '📋', desc: '專業投顧級完整投資策略' },
      { id: 'templates', label: '策略範本', icon: '📚', desc: '投資策略範本庫' },
      { id: 'backtest', label: '回測模擬', icon: '📈', desc: '策略回測模擬' },
      { id: 'simulation', label: '模擬交易', icon: '🎮', desc: '虛擬資金練習交易' },
      { id: 'ml-panel', label: 'ML 模型', icon: '🤖', desc: '機器學習模型訓練與預測' },
    ]
  },
  {
    id: 'portfolio',
    label: '💼 投組',
    defaultSection: 'portfolio',
    items: [
      { id: 'portfolio', label: '投資組合', icon: '💼', desc: '管理你的投資組合' },
      { id: 'transactions', label: '交易記錄', icon: '📊', desc: '持股損益分析' },
      { id: 'categories', label: '股票分類', icon: '📁', desc: '組織追蹤股票' },
      { id: 'diary', label: '投資日記', icon: '📔', desc: '交易筆記與心得' },
      { id: 'risk', label: '風險管理', icon: '🛡️', desc: '倉位計算、停損停利' },
      { id: 'dividend', label: '除權息', icon: '💵', desc: '除權息計算、填息追蹤' },
    ]
  },
  {
    id: 'performance',
    label: '📈 績效',
    defaultSection: 'tracker',
    items: [] // 整合功能，內部使用 Tab 切換
  },
  {
    id: 'alerts',
    label: '🔔 提醒',
    defaultSection: 'alerts',
    items: [] // 整合功能，內部使用 Tab 切換
  },
  {
    id: 'us',
    label: '🇺🇸 美股',
    defaultSection: 'us-stocks',
    items: [] // 獨立功能
  },
];

/**
 * 將群組結構扁平化為 section 列表
 * 用於向後相容現有的 activeSection 邏輯
 */
export const flatSections = menuGroups.flatMap(group => {
  if (group.items.length === 0) {
    // 無子選單的群組
    return [{
      id: group.defaultSection,
      label: group.label,
      groupId: group.id,
    }];
  }
  // 有子選單的群組
  return group.items.map(item => ({
    ...item,
    groupId: group.id,
  }));
});

/**
 * 根據 section ID 找到所屬的群組
 */
export const findGroupBySection = (sectionId) => {
  return menuGroups.find(group =>
    group.defaultSection === sectionId ||
    group.items.some(item => item.id === sectionId)
  );
};

/**
 * 根據 section ID 找到該 section 的詳細資訊
 */
export const findSectionInfo = (sectionId) => {
  for (const group of menuGroups) {
    if (group.items.length === 0 && group.defaultSection === sectionId) {
      return { id: sectionId, label: group.label, groupId: group.id };
    }
    const item = group.items.find(i => i.id === sectionId);
    if (item) {
      return { ...item, groupId: group.id };
    }
  }
  return null;
};

/**
 * 檢查 section ID 是否需要整合渲染
 * (tracker/history-perf 整合為 UnifiedPerformance)
 * (alerts/smart-alerts 整合為 UnifiedAlerts)
 */
export const getUnifiedComponent = (sectionId) => {
  const performanceSections = ['tracker', 'history-perf'];
  const alertSections = ['alerts', 'smart-alerts'];

  if (performanceSections.includes(sectionId)) {
    return 'UnifiedPerformance';
  }
  if (alertSections.includes(sectionId)) {
    return 'UnifiedAlerts';
  }
  return null;
};

export default menuGroups;
