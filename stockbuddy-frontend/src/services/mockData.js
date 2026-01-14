/**
 * mockData.js - 模擬數據中心
 * V10.35 新增
 *
 * 功能：
 * - 集中管理所有模擬數據
 * - API 失敗時提供備援數據
 * - 開發環境測試數據
 */

// ========== 新聞模擬數據 ==========
export const MOCK_NEWS = [
  {
    id: 1,
    title: '台積電法說會報佳音，Q4營收創新高',
    source: '經濟日報',
    time: '2小時前',
    sentiment: 'positive',
    stocks: ['2330'],
    summary: '台積電第四季營收達歷史新高，AI相關營收占比持續上升。',
  },
  {
    id: 2,
    title: '聯發科5G晶片出貨量大增，獲外資調升目標價',
    source: '工商時報',
    time: '3小時前',
    sentiment: 'positive',
    stocks: ['2454'],
    summary: '聯發科5G晶片在新興市場表現亮眼，多家外資調升目標價。',
  },
  {
    id: 3,
    title: '鴻海電動車布局加速，與多家車廠洽談合作',
    source: '自由財經',
    time: '4小時前',
    sentiment: 'neutral',
    stocks: ['2317'],
    summary: '鴻海持續擴大電動車版圖，正與多家國際車廠進行合作洽談。',
  },
  {
    id: 4,
    title: '美債殖利率走升，台股面臨修正壓力',
    source: 'MoneyDJ',
    time: '5小時前',
    sentiment: 'negative',
    stocks: [],
    summary: '美國公債殖利率持續攀升，市場擔憂資金外流，台股承壓。',
  },
  {
    id: 5,
    title: '航運股利多，歐洲線運價連續上漲',
    source: '經濟日報',
    time: '6小時前',
    sentiment: 'positive',
    stocks: ['2603', '2609'],
    summary: '紅海危機持續，歐洲線運價連續三週上漲，航運股受惠。',
  },
];

// ========== 歷史績效模擬數據 ==========
export const MOCK_PERFORMANCE_HISTORY = [
  { date: '2024-01-02', accuracy: 68, avgReturn: 2.3, recommendations: 15 },
  { date: '2024-01-03', accuracy: 72, avgReturn: 1.8, recommendations: 12 },
  { date: '2024-01-04', accuracy: 65, avgReturn: -0.5, recommendations: 18 },
  { date: '2024-01-05', accuracy: 70, avgReturn: 1.2, recommendations: 14 },
  { date: '2024-01-08', accuracy: 75, avgReturn: 3.1, recommendations: 16 },
  { date: '2024-01-09', accuracy: 78, avgReturn: 2.5, recommendations: 13 },
  { date: '2024-01-10', accuracy: 71, avgReturn: 1.9, recommendations: 17 },
];

// ========== 形態辨識模擬數據 ==========
export const MOCK_PATTERNS = [
  {
    id: 1,
    stockId: '2330',
    stockName: '台積電',
    pattern: 'ascending_triangle',
    patternName: '上升三角形',
    type: 'bullish',
    confidence: 85,
    targetPrice: 650,
    stopLoss: 580,
    currentPrice: 610,
    status: 'forming',
    reliability: 72,
    detected: '2024-01-10',
  },
  {
    id: 2,
    stockId: '2454',
    stockName: '聯發科',
    pattern: 'double_bottom',
    patternName: '雙重底',
    type: 'bullish',
    confidence: 78,
    targetPrice: 980,
    stopLoss: 850,
    currentPrice: 920,
    status: 'confirmed',
    reliability: 68,
    detected: '2024-01-08',
  },
  {
    id: 3,
    stockId: '2317',
    stockName: '鴻海',
    pattern: 'head_shoulders',
    patternName: '頭肩頂',
    type: 'bearish',
    confidence: 72,
    targetPrice: 95,
    stopLoss: 115,
    currentPrice: 108,
    status: 'forming',
    reliability: 65,
    detected: '2024-01-09',
  },
];

// ========== 進階圖表模擬數據 ==========
export const MOCK_SECTOR_DATA = [
  { name: '半導體', value: 35, change: 2.5, color: '#3B82F6' },
  { name: '電子零組件', value: 20, change: -1.2, color: '#10B981' },
  { name: '金融', value: 18, change: 0.8, color: '#F59E0B' },
  { name: '傳產', value: 12, change: -0.5, color: '#EF4444' },
  { name: '航運', value: 8, change: 3.2, color: '#8B5CF6' },
  { name: '其他', value: 7, change: 0.3, color: '#6B7280' },
];

export const MOCK_CORRELATION_DATA = [
  ['', '台積電', '聯發科', '鴻海', '大立光', '台達電'],
  ['台積電', 1.0, 0.75, 0.42, 0.68, 0.55],
  ['聯發科', 0.75, 1.0, 0.38, 0.72, 0.48],
  ['鴻海', 0.42, 0.38, 1.0, 0.25, 0.62],
  ['大立光', 0.68, 0.72, 0.25, 1.0, 0.35],
  ['台達電', 0.55, 0.48, 0.62, 0.35, 1.0],
];

// ========== 模擬交易用股票清單 ==========
export const MOCK_STOCK_LIST = [
  { stock_id: '2330', name: '台積電', price: 610, change: 1.2 },
  { stock_id: '2454', name: '聯發科', price: 920, change: 2.5 },
  { stock_id: '2317', name: '鴻海', price: 108, change: -0.8 },
  { stock_id: '2412', name: '中華電', price: 118, change: 0.3 },
  { stock_id: '2308', name: '台達電', price: 325, change: 1.8 },
  { stock_id: '2881', name: '富邦金', price: 72, change: -0.5 },
  { stock_id: '2882', name: '國泰金', price: 48, change: 0.2 },
  { stock_id: '2603', name: '長榮', price: 185, change: 3.2 },
];

// ========== 數據獲取輔助函數 ==========

/**
 * 安全獲取數據（API 失敗時返回 mock）
 */
export const safeGetData = async (apiCall, mockData, defaultValue = []) => {
  try {
    const response = await apiCall();
    if (response.success && response.data) {
      return response.data;
    }
    return mockData || defaultValue;
  } catch (error) {
    console.warn('API call failed, using mock data:', error.message);
    return mockData || defaultValue;
  }
};

export default {
  news: MOCK_NEWS,
  performanceHistory: MOCK_PERFORMANCE_HISTORY,
  patterns: MOCK_PATTERNS,
  sectorData: MOCK_SECTOR_DATA,
  correlationData: MOCK_CORRELATION_DATA,
  stockList: MOCK_STOCK_LIST,
  safeGetData,
};
