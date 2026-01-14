/**
 * InvestmentDiary.jsx - 投資日記
 * V10.33 新增
 *
 * 功能：
 * - 交易筆記記錄
 * - 投資心得分享
 * - 錯誤檢討記錄
 * - 學習成長追蹤
 */

import React, { useState, useMemo } from 'react';

// 儲存鍵
const DIARY_KEY = 'stockbuddy_diary';

// 日記類型
const DIARY_TYPES = [
  { id: 'trade', label: '交易筆記', icon: '💹', color: 'text-blue-400', bg: 'bg-blue-500/20' },
  { id: 'analysis', label: '分析記錄', icon: '📊', color: 'text-purple-400', bg: 'bg-purple-500/20' },
  { id: 'review', label: '錯誤檢討', icon: '❌', color: 'text-red-400', bg: 'bg-red-500/20' },
  { id: 'learning', label: '學習心得', icon: '📚', color: 'text-emerald-400', bg: 'bg-emerald-500/20' },
  { id: 'insight', label: '市場觀察', icon: '👁️', color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
];

// 情緒標籤
const EMOTION_TAGS = [
  { id: 'confident', label: '自信', icon: '💪' },
  { id: 'worried', label: '擔憂', icon: '😟' },
  { id: 'excited', label: '興奮', icon: '🤩' },
  { id: 'regret', label: '後悔', icon: '😢' },
  { id: 'calm', label: '冷靜', icon: '😌' },
  { id: 'greedy', label: '貪婪', icon: '🤑' },
  { id: 'fearful', label: '恐懼', icon: '😨' },
];

// 取得日記
const getDiaries = () => {
  try {
    return JSON.parse(localStorage.getItem(DIARY_KEY) || '[]');
  } catch {
    return [];
  }
};

// 儲存日記
const saveDiary = (diary) => {
  const diaries = getDiaries();
  const newDiary = {
    ...diary,
    id: Date.now(),
    createdAt: new Date().toISOString(),
  };
  diaries.unshift(newDiary);
  localStorage.setItem(DIARY_KEY, JSON.stringify(diaries));
  return newDiary;
};

// 刪除日記
const deleteDiary = (id) => {
  const diaries = getDiaries().filter(d => d.id !== id);
  localStorage.setItem(DIARY_KEY, JSON.stringify(diaries));
};

const InvestmentDiary = () => {
  const [diaries, setDiaries] = useState(getDiaries);
  const [showForm, setShowForm] = useState(false);
  const [filterType, setFilterType] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // 表單狀態
  const [formData, setFormData] = useState({
    type: 'trade',
    title: '',
    content: '',
    stocks: '',
    emotions: [],
    tags: '',
  });

  // 篩選日記
  const filteredDiaries = useMemo(() => {
    let result = [...diaries];

    if (filterType !== 'all') {
      result = result.filter(d => d.type === filterType);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(d =>
        d.title?.toLowerCase().includes(term) ||
        d.content?.toLowerCase().includes(term) ||
        d.stocks?.toLowerCase().includes(term)
      );
    }

    return result;
  }, [diaries, filterType, searchTerm]);

  // 日記統計
  const stats = useMemo(() => {
    const totalCount = diaries.length;
    const thisMonth = diaries.filter(d => {
      const date = new Date(d.createdAt);
      const now = new Date();
      return date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
    }).length;

    const emotionCounts = {};
    diaries.forEach(d => {
      d.emotions?.forEach(e => {
        emotionCounts[e] = (emotionCounts[e] || 0) + 1;
      });
    });

    const topEmotion = Object.entries(emotionCounts).sort((a, b) => b[1] - a[1])[0];

    return { totalCount, thisMonth, topEmotion };
  }, [diaries]);

  // 處理表單提交
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.content.trim()) return;

    const newDiary = saveDiary(formData);
    setDiaries([newDiary, ...diaries]);
    setFormData({
      type: 'trade',
      title: '',
      content: '',
      stocks: '',
      emotions: [],
      tags: '',
    });
    setShowForm(false);
  };

  // 處理刪除
  const handleDelete = (id) => {
    if (window.confirm('確定要刪除此筆記嗎？')) {
      deleteDiary(id);
      setDiaries(diaries.filter(d => d.id !== id));
    }
  };

  // 格式化日期
  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // 切換情緒標籤
  const toggleEmotion = (emotionId) => {
    setFormData(prev => ({
      ...prev,
      emotions: prev.emotions.includes(emotionId)
        ? prev.emotions.filter(e => e !== emotionId)
        : [...prev.emotions, emotionId],
    }));
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>📔</span>
          <span>投資日記</span>
        </h2>

        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
        >
          <span>{showForm ? '✕' : '✍️'}</span>
          <span>{showForm ? '取消' : '寫日記'}</span>
        </button>
      </div>

      {/* 統計卡片 */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
          <div className="text-slate-400 text-xs mb-1">總筆記數</div>
          <div className="text-2xl font-bold text-white">{stats.totalCount}</div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
          <div className="text-slate-400 text-xs mb-1">本月新增</div>
          <div className="text-2xl font-bold text-blue-400">{stats.thisMonth}</div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
          <div className="text-slate-400 text-xs mb-1">最常情緒</div>
          <div className="text-2xl">
            {stats.topEmotion
              ? EMOTION_TAGS.find(e => e.id === stats.topEmotion[0])?.icon || '😊'
              : '—'}
          </div>
        </div>
      </div>

      {/* 新增日記表單 */}
      {showForm && (
        <form onSubmit={handleSubmit} className="mb-6 p-4 bg-slate-700/30 rounded-lg">
          <h4 className="text-white font-medium mb-4">新增筆記</h4>

          {/* 類型選擇 */}
          <div className="mb-4">
            <label className="text-slate-400 text-sm mb-2 block">筆記類型</label>
            <div className="flex flex-wrap gap-2">
              {DIARY_TYPES.map(type => (
                <button
                  key={type.id}
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, type: type.id }))}
                  className={`px-3 py-1.5 rounded-lg text-sm transition-colors flex items-center gap-1 ${
                    formData.type === type.id
                      ? `${type.bg} ${type.color}`
                      : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'
                  }`}
                >
                  <span>{type.icon}</span>
                  <span>{type.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 標題 */}
          <div className="mb-4">
            <label className="text-slate-400 text-sm mb-2 block">標題</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              placeholder="今日交易心得..."
              className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* 相關股票 */}
          <div className="mb-4">
            <label className="text-slate-400 text-sm mb-2 block">相關股票 (選填)</label>
            <input
              type="text"
              value={formData.stocks}
              onChange={(e) => setFormData(prev => ({ ...prev, stocks: e.target.value }))}
              placeholder="2330, 台積電"
              className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* 內容 */}
          <div className="mb-4">
            <label className="text-slate-400 text-sm mb-2 block">內容</label>
            <textarea
              value={formData.content}
              onChange={(e) => setFormData(prev => ({ ...prev, content: e.target.value }))}
              placeholder="詳細記錄你的想法..."
              rows={5}
              className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none resize-none"
            />
          </div>

          {/* 情緒標籤 */}
          <div className="mb-4">
            <label className="text-slate-400 text-sm mb-2 block">當時情緒 (可多選)</label>
            <div className="flex flex-wrap gap-2">
              {EMOTION_TAGS.map(emotion => (
                <button
                  key={emotion.id}
                  type="button"
                  onClick={() => toggleEmotion(emotion.id)}
                  className={`px-3 py-1.5 rounded-lg text-sm transition-colors flex items-center gap-1 ${
                    formData.emotions.includes(emotion.id)
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/50'
                      : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'
                  }`}
                >
                  <span>{emotion.icon}</span>
                  <span>{emotion.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 提交按鈕 */}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={!formData.title.trim() || !formData.content.trim()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-lg font-medium transition-colors"
            >
              儲存筆記
            </button>
          </div>
        </form>
      )}

      {/* 篩選與搜尋 */}
      <div className="flex flex-wrap gap-4 mb-6">
        {/* 類型篩選 */}
        <div className="flex gap-2">
          <button
            onClick={() => setFilterType('all')}
            className={`px-3 py-1.5 rounded-lg text-sm ${
              filterType === 'all'
                ? 'bg-slate-600 text-white'
                : 'bg-slate-700/50 text-slate-400'
            }`}
          >
            全部
          </button>
          {DIARY_TYPES.map(type => (
            <button
              key={type.id}
              onClick={() => setFilterType(type.id)}
              className={`px-3 py-1.5 rounded-lg text-sm flex items-center gap-1 ${
                filterType === type.id
                  ? `${type.bg} ${type.color}`
                  : 'bg-slate-700/50 text-slate-400'
              }`}
            >
              <span>{type.icon}</span>
            </button>
          ))}
        </div>

        {/* 搜尋 */}
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="搜尋筆記..."
            className="w-full px-4 py-1.5 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none text-sm"
          />
        </div>
      </div>

      {/* 日記列表 */}
      <div className="space-y-4 max-h-[500px] overflow-y-auto">
        {filteredDiaries.length > 0 ? (
          filteredDiaries.map(diary => {
            const typeInfo = DIARY_TYPES.find(t => t.id === diary.type) || DIARY_TYPES[0];

            return (
              <div key={diary.id} className="bg-slate-700/30 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${typeInfo.bg} ${typeInfo.color}`}>
                      {typeInfo.icon} {typeInfo.label}
                    </span>
                    <span className="text-slate-500 text-xs">{formatDate(diary.createdAt)}</span>
                  </div>
                  <button
                    onClick={() => handleDelete(diary.id)}
                    className="text-slate-500 hover:text-red-400 transition-colors"
                  >
                    🗑️
                  </button>
                </div>

                <h4 className="text-white font-medium mb-2">{diary.title}</h4>

                {diary.stocks && (
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-slate-500 text-xs">相關股票:</span>
                    <span className="text-blue-400 text-sm">{diary.stocks}</span>
                  </div>
                )}

                <p className="text-slate-300 text-sm whitespace-pre-wrap mb-3">{diary.content}</p>

                {diary.emotions?.length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500 text-xs">情緒:</span>
                    <div className="flex gap-1">
                      {diary.emotions.map(emotionId => {
                        const emotion = EMOTION_TAGS.find(e => e.id === emotionId);
                        return emotion ? (
                          <span key={emotionId} title={emotion.label}>{emotion.icon}</span>
                        ) : null;
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="text-center py-12">
            <span className="text-5xl">📝</span>
            <p className="text-slate-400 mt-3">還沒有任何筆記</p>
            <p className="text-slate-500 text-sm mt-1">點擊「寫日記」開始記錄你的投資歷程</p>
          </div>
        )}
      </div>

      {/* 提示說明 */}
      <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <div className="flex items-start gap-2">
          <span className="text-blue-400">💡</span>
          <div className="text-blue-300 text-sm">
            <p className="font-medium mb-1">投資日記的好處</p>
            <ul className="text-xs space-y-0.5 text-blue-300/80">
              <li>- 記錄交易決策，日後回顧學習</li>
              <li>- 追蹤情緒變化，避免衝動交易</li>
              <li>- 累積市場觀察，提升投資敏銳度</li>
              <li>- 檢討錯誤經驗，持續進步成長</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InvestmentDiary;
