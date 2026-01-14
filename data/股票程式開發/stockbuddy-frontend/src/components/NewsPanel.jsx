/**
 * NewsPanel.jsx - 新聞整合面板
 * V10.32 新增
 * V10.35.2 更新：添加數據來源標示
 *
 * 功能：
 * - 即時新聞串流
 * - 個股相關新聞
 * - 新聞分類過濾
 * - 新聞情緒分析
 */

import React, { useState, useMemo } from 'react';

// 數據來源標示組件
const DataSourceBadge = ({ isDemo = true }) => (
  <span className={`px-2 py-0.5 rounded text-xs ${
    isDemo
      ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
      : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
  }`}>
    {isDemo ? '示範數據' : '即時數據'}
  </span>
);

// 模擬新聞數據
const MOCK_NEWS = [
  {
    id: 1,
    title: '台積電法說會釋樂觀展望 Q1營收估季增5%',
    source: '工商時報',
    time: '10 分鐘前',
    category: 'earnings',
    sentiment: 'positive',
    stocks: ['2330'],
    summary: '台積電昨日舉行法說會，對於第一季營收展望樂觀，預估季增約5%...',
    url: '#',
  },
  {
    id: 2,
    title: 'AI伺服器需求強勁 聯發科訂單爆滿',
    source: '經濟日報',
    time: '25 分鐘前',
    category: 'industry',
    sentiment: 'positive',
    stocks: ['2454'],
    summary: '受惠於AI伺服器需求持續強勁，聯發科客戶訂單爆滿，預期今年營收將...',
    url: '#',
  },
  {
    id: 3,
    title: '外資連續買超台股 三大法人買超150億',
    source: '鉅亨網',
    time: '45 分鐘前',
    category: 'market',
    sentiment: 'positive',
    stocks: [],
    summary: '外資今日持續買超台股，三大法人合計買超約150億元，集中火力鎖定...',
    url: '#',
  },
  {
    id: 4,
    title: '美國聯準會暗示降息腳步放緩 市場觀望',
    source: 'Bloomberg',
    time: '1 小時前',
    category: 'global',
    sentiment: 'neutral',
    stocks: [],
    summary: '美國聯準會最新會議紀要顯示，委員們對於降息步伐意見分歧...',
    url: '#',
  },
  {
    id: 5,
    title: '鴻海印度廠傳擴產 EV電池布局加速',
    source: '自由財經',
    time: '1.5 小時前',
    category: 'company',
    sentiment: 'positive',
    stocks: ['2317'],
    summary: '鴻海印度廠傳出將擴產計畫，同時加速電動車電池布局，目標...',
    url: '#',
  },
  {
    id: 6,
    title: '金管會示警：投信高額配息基金風險',
    source: '中央社',
    time: '2 小時前',
    category: 'regulation',
    sentiment: 'negative',
    stocks: [],
    summary: '金管會今日發布警示，提醒投資人注意高配息基金可能存在的風險...',
    url: '#',
  },
  {
    id: 7,
    title: '台塑四寶Q4財報出爐 石化景氣待復甦',
    source: '工商時報',
    time: '3 小時前',
    category: 'earnings',
    sentiment: 'neutral',
    stocks: ['1301', '1303', '1326', '6505'],
    summary: '台塑四寶第四季財報出爐，受國際油價波動影響，整體表現持平...',
    url: '#',
  },
  {
    id: 8,
    title: '航運股走弱 長榮、陽明跌幅超過2%',
    source: '經濟日報',
    time: '4 小時前',
    category: 'industry',
    sentiment: 'negative',
    stocks: ['2603', '2609'],
    summary: '航運類股今日表現疲弱，長榮、陽明跌幅均超過2%，市場擔憂...',
    url: '#',
  },
];

// 新聞分類
const NEWS_CATEGORIES = [
  { id: 'all', label: '全部', icon: '📰' },
  { id: 'market', label: '大盤', icon: '📊' },
  { id: 'industry', label: '產業', icon: '🏭' },
  { id: 'company', label: '公司', icon: '🏢' },
  { id: 'earnings', label: '財報', icon: '💰' },
  { id: 'global', label: '國際', icon: '🌍' },
  { id: 'regulation', label: '法規', icon: '⚖️' },
];

// 情緒顏色
const SENTIMENT_STYLES = {
  positive: { color: 'text-red-400', bg: 'bg-red-500/20', label: '利多', icon: '📈' },
  negative: { color: 'text-emerald-400', bg: 'bg-emerald-500/20', label: '利空', icon: '📉' },
  neutral: { color: 'text-slate-400', bg: 'bg-slate-500/20', label: '中立', icon: '➖' },
};

const NewsPanel = ({ watchlist = [], selectedStock = null }) => {
  const [activeCategory, setActiveCategory] = useState('all');
  const [sentimentFilter, setSentimentFilter] = useState('all');
  const [showRelatedOnly, setShowRelatedOnly] = useState(false);

  // 篩選新聞
  const filteredNews = useMemo(() => {
    let news = [...MOCK_NEWS];

    // 分類篩選
    if (activeCategory !== 'all') {
      news = news.filter(n => n.category === activeCategory);
    }

    // 情緒篩選
    if (sentimentFilter !== 'all') {
      news = news.filter(n => n.sentiment === sentimentFilter);
    }

    // 只顯示相關新聞
    if (showRelatedOnly && (selectedStock || watchlist.length > 0)) {
      const relevantStocks = selectedStock
        ? [selectedStock.stock_id]
        : watchlist.map(s => s.stock_id);
      news = news.filter(n =>
        n.stocks.some(s => relevantStocks.includes(s)) || n.stocks.length === 0
      );
    }

    return news;
  }, [activeCategory, sentimentFilter, showRelatedOnly, selectedStock, watchlist]);

  // 新聞卡片
  const NewsCard = ({ news }) => {
    const sentiment = SENTIMENT_STYLES[news.sentiment];

    return (
      <div className="bg-slate-700/30 rounded-lg p-4 hover:bg-slate-700/50 transition-colors cursor-pointer">
        <div className="flex items-start gap-3">
          {/* 情緒圖示 */}
          <div className={`p-2 rounded-lg ${sentiment.bg}`}>
            <span className="text-lg">{sentiment.icon}</span>
          </div>

          <div className="flex-1 min-w-0">
            {/* 標題 */}
            <h4 className="text-white font-medium mb-1 line-clamp-2">{news.title}</h4>

            {/* 摘要 */}
            <p className="text-slate-400 text-sm line-clamp-2 mb-2">{news.summary}</p>

            {/* 元資訊 */}
            <div className="flex items-center gap-3 text-xs">
              <span className="text-slate-500">{news.source}</span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-500">{news.time}</span>
              <span className={`px-1.5 py-0.5 rounded ${sentiment.bg} ${sentiment.color}`}>
                {sentiment.label}
              </span>
            </div>

            {/* 相關股票 */}
            {news.stocks.length > 0 && (
              <div className="flex items-center gap-2 mt-2">
                <span className="text-slate-500 text-xs">相關：</span>
                <div className="flex gap-1">
                  {news.stocks.map(stockId => (
                    <span
                      key={stockId}
                      className="px-1.5 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded"
                    >
                      {stockId}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>📰</span>
            <span>即時財經新聞</span>
          </h2>
          <DataSourceBadge isDemo={true} />
        </div>

        {/* 相關新聞開關 */}
        {(selectedStock || watchlist.length > 0) && (
          <button
            onClick={() => setShowRelatedOnly(!showRelatedOnly)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              showRelatedOnly
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-400 hover:text-white'
            }`}
          >
            {showRelatedOnly ? '✓ 只看相關' : '只看相關'}
          </button>
        )}
      </div>

      {/* 分類篩選 */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
        {NEWS_CATEGORIES.map(cat => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors flex items-center gap-1.5 ${
              activeCategory === cat.id
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'
            }`}
          >
            <span>{cat.icon}</span>
            <span>{cat.label}</span>
          </button>
        ))}
      </div>

      {/* 情緒篩選 */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setSentimentFilter('all')}
          className={`px-3 py-1 rounded text-xs ${
            sentimentFilter === 'all'
              ? 'bg-slate-600 text-white'
              : 'bg-slate-700/50 text-slate-400'
          }`}
        >
          全部
        </button>
        {Object.entries(SENTIMENT_STYLES).map(([key, style]) => (
          <button
            key={key}
            onClick={() => setSentimentFilter(key)}
            className={`px-3 py-1 rounded text-xs flex items-center gap-1 ${
              sentimentFilter === key
                ? `${style.bg} ${style.color}`
                : 'bg-slate-700/50 text-slate-400'
            }`}
          >
            <span>{style.icon}</span>
            <span>{style.label}</span>
          </button>
        ))}
      </div>

      {/* 新聞列表 */}
      <div className="space-y-3 max-h-[600px] overflow-y-auto">
        {filteredNews.length > 0 ? (
          filteredNews.map(news => (
            <NewsCard key={news.id} news={news} />
          ))
        ) : (
          <div className="text-center py-8">
            <span className="text-4xl">📭</span>
            <p className="text-slate-400 mt-2">沒有符合條件的新聞</p>
          </div>
        )}
      </div>

      {/* 新聞統計 */}
      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-500">共 {filteredNews.length} 則新聞</span>
          <div className="flex items-center gap-4">
            <span className="text-red-400">
              📈 {MOCK_NEWS.filter(n => n.sentiment === 'positive').length} 利多
            </span>
            <span className="text-emerald-400">
              📉 {MOCK_NEWS.filter(n => n.sentiment === 'negative').length} 利空
            </span>
            <span className="text-slate-400">
              ➖ {MOCK_NEWS.filter(n => n.sentiment === 'neutral').length} 中立
            </span>
          </div>
        </div>
      </div>

      {/* 說明 */}
      <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <div className="flex items-start gap-2">
          <span className="text-blue-400">ℹ️</span>
          <div className="text-blue-300 text-sm">
            <p className="font-medium mb-1">新聞說明</p>
            <ul className="text-xs space-y-0.5 text-blue-300/80">
              <li>- 新聞情緒由 AI 分析判斷利多/利空/中立</li>
              <li>- 可篩選分類或情緒快速找到相關資訊</li>
              <li>- 點擊新聞可查看完整內容</li>
              <li>- 新聞僅供參考，不構成投資建議</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

// 新聞速報組件（用於側邊欄）
export const NewsTicker = () => {
  const [currentIndex, setCurrentIndex] = useState(0);

  React.useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex(prev => (prev + 1) % MOCK_NEWS.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const news = MOCK_NEWS[currentIndex];
  const sentiment = SENTIMENT_STYLES[news.sentiment];

  return (
    <div className="bg-slate-800/50 rounded-lg p-3 overflow-hidden">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-red-500 animate-pulse">●</span>
        <span className="text-slate-400 text-xs">即時新聞</span>
      </div>
      <div className="flex items-start gap-2">
        <span className={sentiment.color}>{sentiment.icon}</span>
        <p className="text-white text-sm line-clamp-2 flex-1">{news.title}</p>
      </div>
      <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
        <span>{news.source}</span>
        <span>{news.time}</span>
      </div>
    </div>
  );
};

export default NewsPanel;
