/**
 * MarketCalendar.jsx - 市場行事曆
 * V10.27 新增
 * V10.35.2 更新：添加數據來源標示
 *
 * 功能：
 * - 除權息日期
 * - 財報公布日期
 * - 重大經濟數據發布
 * - 台美股市休市日
 * - 自訂提醒事件
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { API_STOCKS_BASE } from '../config';

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

const API_BASE = API_STOCKS_BASE;

// 2026 年台股休市日期（農曆新年、清明、端午、中秋等）
const TW_HOLIDAYS_2026 = [
  { date: '2026-01-01', name: '元旦' },
  { date: '2026-01-29', name: '農曆除夕' },
  { date: '2026-01-30', name: '春節' },
  { date: '2026-01-31', name: '春節' },
  { date: '2026-02-01', name: '春節' },
  { date: '2026-02-02', name: '春節' },
  { date: '2026-02-27', name: '和平紀念日補假' },
  { date: '2026-02-28', name: '和平紀念日' },
  { date: '2026-04-04', name: '兒童節/清明節' },
  { date: '2026-04-05', name: '清明節' },
  { date: '2026-04-06', name: '清明節補假' },
  { date: '2026-05-01', name: '勞動節' },
  { date: '2026-05-31', name: '端午節' },
  { date: '2026-10-01', name: '中秋節' },
  { date: '2026-10-10', name: '國慶日' },
];

// 2026 年美股休市日期
const US_HOLIDAYS_2026 = [
  { date: '2026-01-01', name: "New Year's Day" },
  { date: '2026-01-19', name: 'Martin Luther King Jr. Day' },
  { date: '2026-02-16', name: "Presidents' Day" },
  { date: '2026-04-03', name: 'Good Friday' },
  { date: '2026-05-25', name: 'Memorial Day' },
  { date: '2026-06-19', name: 'Juneteenth' },
  { date: '2026-07-03', name: 'Independence Day (Observed)' },
  { date: '2026-09-07', name: 'Labor Day' },
  { date: '2026-11-26', name: 'Thanksgiving Day' },
  { date: '2026-12-25', name: 'Christmas Day' },
];

// 事件類型顏色
const EVENT_COLORS = {
  earnings: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  dividend: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  economic: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  holiday_tw: 'bg-red-500/20 text-red-400 border-red-500/30',
  holiday_us: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  custom: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

const EVENT_ICONS = {
  earnings: '📊',
  dividend: '💰',
  economic: '📈',
  holiday_tw: '🇹🇼',
  holiday_us: '🇺🇸',
  custom: '📌',
};

const MarketCalendar = ({ watchlist = [] }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(null);
  const [events, setEvents] = useState([]);
  const [dividendEvents, setDividendEvents] = useState([]);
  const [showEventModal, setShowEventModal] = useState(false);
  const [customEvents, setCustomEvents] = useState([]);
  const [newEvent, setNewEvent] = useState({ title: '', date: '', type: 'custom' });
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('calendar');

  // 從 localStorage 載入自訂事件
  useEffect(() => {
    const saved = localStorage.getItem('stockbuddy_custom_events');
    if (saved) {
      try {
        setCustomEvents(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to load custom events:', e);
      }
    }
  }, []);

  // 儲存自訂事件
  const saveCustomEvents = (events) => {
    setCustomEvents(events);
    localStorage.setItem('stockbuddy_custom_events', JSON.stringify(events));
  };

  // 取得除權息資料（模擬）
  const fetchDividendData = useCallback(async () => {
    setLoading(true);
    try {
      // 這裡可以接入實際的 API
      // 模擬一些除權息事件
      const mockDividends = [
        { stockId: '2330', name: '台積電', date: '2026-01-15', type: 'dividend', dividend: 3.5 },
        { stockId: '2317', name: '鴻海', date: '2026-01-20', type: 'dividend', dividend: 5.0 },
        { stockId: '2454', name: '聯發科', date: '2026-02-10', type: 'dividend', dividend: 20 },
        { stockId: '3008', name: '大立光', date: '2026-02-25', type: 'dividend', dividend: 50 },
      ];
      setDividendEvents(mockDividends);
    } catch (e) {
      console.error('Error fetching dividend data:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDividendData();
  }, [fetchDividendData]);

  // 組合所有事件
  const allEvents = useMemo(() => {
    const combined = [];

    // 台股休市
    TW_HOLIDAYS_2026.forEach((h) => {
      combined.push({
        id: `tw_${h.date}`,
        date: h.date,
        title: h.name,
        type: 'holiday_tw',
        market: 'TW',
      });
    });

    // 美股休市
    US_HOLIDAYS_2026.forEach((h) => {
      combined.push({
        id: `us_${h.date}`,
        date: h.date,
        title: h.name,
        type: 'holiday_us',
        market: 'US',
      });
    });

    // 除權息
    dividendEvents.forEach((d, i) => {
      combined.push({
        id: `div_${i}`,
        date: d.date,
        title: `${d.name} 除息 $${d.dividend}`,
        type: 'dividend',
        stockId: d.stockId,
      });
    });

    // 自訂事件
    customEvents.forEach((e, i) => {
      combined.push({
        ...e,
        id: e.id || `custom_${i}`,
      });
    });

    return combined;
  }, [dividendEvents, customEvents]);

  // 取得指定月份的日曆資料
  const getCalendarDays = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    const days = [];
    const startPadding = firstDay.getDay(); // 0 = Sunday

    // 上個月的日期（補齊第一週）
    for (let i = startPadding - 1; i >= 0; i--) {
      const date = new Date(year, month, -i);
      days.push({
        date,
        dateStr: date.toISOString().split('T')[0],
        isCurrentMonth: false,
        isToday: false,
      });
    }

    // 本月日期
    const today = new Date().toISOString().split('T')[0];
    for (let d = 1; d <= lastDay.getDate(); d++) {
      const date = new Date(year, month, d);
      const dateStr = date.toISOString().split('T')[0];
      days.push({
        date,
        dateStr,
        isCurrentMonth: true,
        isToday: dateStr === today,
        isWeekend: date.getDay() === 0 || date.getDay() === 6,
      });
    }

    // 下個月日期（補齊最後一週）
    const remaining = 42 - days.length; // 6 rows x 7 days
    for (let i = 1; i <= remaining; i++) {
      const date = new Date(year, month + 1, i);
      days.push({
        date,
        dateStr: date.toISOString().split('T')[0],
        isCurrentMonth: false,
        isToday: false,
      });
    }

    return days;
  }, [currentDate]);

  // 取得指定日期的事件
  const getEventsForDate = (dateStr) => {
    return allEvents.filter((e) => e.date === dateStr);
  };

  // 月份導航
  const navigateMonth = (direction) => {
    setCurrentDate((prev) => {
      const newDate = new Date(prev);
      newDate.setMonth(newDate.getMonth() + direction);
      return newDate;
    });
  };

  // 新增自訂事件
  const handleAddEvent = () => {
    if (!newEvent.title || !newEvent.date) return;

    const event = {
      id: `custom_${Date.now()}`,
      ...newEvent,
      type: 'custom',
    };

    saveCustomEvents([...customEvents, event]);
    setNewEvent({ title: '', date: '', type: 'custom' });
    setShowEventModal(false);
  };

  // 刪除自訂事件
  const handleDeleteEvent = (eventId) => {
    const updated = customEvents.filter((e) => e.id !== eventId);
    saveCustomEvents(updated);
  };

  // 取得即將到來的事件
  const upcomingEvents = useMemo(() => {
    const today = new Date().toISOString().split('T')[0];
    return allEvents
      .filter((e) => e.date >= today)
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(0, 10);
  }, [allEvents]);

  // 渲染日曆格子
  const renderCalendarCell = (day) => {
    const events = getEventsForDate(day.dateStr);
    const hasEvents = events.length > 0;
    const isSelected = selectedDate === day.dateStr;

    return (
      <div
        key={day.dateStr}
        onClick={() => setSelectedDate(day.dateStr)}
        className={`
          min-h-[80px] p-1 border border-slate-700/50 cursor-pointer transition-all
          ${day.isCurrentMonth ? 'bg-slate-800/50' : 'bg-slate-900/30'}
          ${day.isToday ? 'ring-2 ring-blue-500' : ''}
          ${isSelected ? 'bg-slate-700' : 'hover:bg-slate-700/50'}
          ${day.isWeekend ? 'bg-slate-800/30' : ''}
        `}
      >
        <div
          className={`
          text-sm font-medium mb-1
          ${day.isCurrentMonth ? 'text-white' : 'text-slate-600'}
          ${day.isToday ? 'text-blue-400' : ''}
        `}
        >
          {day.date.getDate()}
        </div>
        {hasEvents && (
          <div className="space-y-0.5">
            {events.slice(0, 2).map((event) => (
              <div
                key={event.id}
                className={`text-xs px-1 py-0.5 rounded truncate border ${EVENT_COLORS[event.type]}`}
                title={event.title}
              >
                {EVENT_ICONS[event.type]} {event.title.slice(0, 8)}
              </div>
            ))}
            {events.length > 2 && (
              <div className="text-xs text-slate-500">+{events.length - 2} 更多</div>
            )}
          </div>
        )}
      </div>
    );
  };

  // 渲染事件列表
  const renderEventList = () => {
    const dateEvents = selectedDate ? getEventsForDate(selectedDate) : upcomingEvents;
    const title = selectedDate ? `${selectedDate} 事件` : '即將到來的事件';

    return (
      <div className="bg-slate-800/50 rounded-lg p-4">
        <h3 className="text-white font-medium mb-3">{title}</h3>
        {dateEvents.length === 0 ? (
          <div className="text-slate-500 text-center py-4">沒有事件</div>
        ) : (
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {dateEvents.map((event) => (
              <div
                key={event.id}
                className={`flex items-center justify-between p-3 rounded-lg border ${EVENT_COLORS[event.type]}`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">{EVENT_ICONS[event.type]}</span>
                  <div>
                    <div className="text-white font-medium">{event.title}</div>
                    <div className="text-xs opacity-70">{event.date}</div>
                  </div>
                </div>
                {event.type === 'custom' && (
                  <button
                    onClick={() => handleDeleteEvent(event.id)}
                    className="text-slate-400 hover:text-red-400 p-1"
                    title="刪除"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // 渲染休市總覽
  const renderHolidayOverview = () => (
    <div className="grid md:grid-cols-2 gap-4">
      {/* 台股休市 */}
      <div className="bg-slate-800/50 rounded-lg p-4">
        <h3 className="text-white font-medium mb-3 flex items-center gap-2">
          <span>🇹🇼</span> 2026 台股休市日
        </h3>
        <div className="space-y-2 max-h-[300px] overflow-y-auto">
          {TW_HOLIDAYS_2026.map((h) => (
            <div
              key={h.date}
              className="flex items-center justify-between p-2 bg-red-500/10 rounded border border-red-500/20"
            >
              <span className="text-red-400">{h.name}</span>
              <span className="text-slate-400 text-sm">{h.date}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 美股休市 */}
      <div className="bg-slate-800/50 rounded-lg p-4">
        <h3 className="text-white font-medium mb-3 flex items-center gap-2">
          <span>🇺🇸</span> 2026 美股休市日
        </h3>
        <div className="space-y-2 max-h-[300px] overflow-y-auto">
          {US_HOLIDAYS_2026.map((h) => (
            <div
              key={h.date}
              className="flex items-center justify-between p-2 bg-purple-500/10 rounded border border-purple-500/20"
            >
              <span className="text-purple-400">{h.name}</span>
              <span className="text-slate-400 text-sm">{h.date}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
      {/* 標題列 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>📅</span> 市場行事曆
          </h2>
          <DataSourceBadge isDemo={true} />
        </div>
        <button
          onClick={() => setShowEventModal(true)}
          className="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-lg transition-colors"
        >
          + 新增提醒
        </button>
      </div>

      {/* 分頁 */}
      <div className="flex gap-2 mb-4">
        {[
          { key: 'calendar', label: '月曆', icon: '📆' },
          { key: 'upcoming', label: '即將到來', icon: '⏰' },
          { key: 'holidays', label: '休市總覽', icon: '🏖️' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'bg-blue-500 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* 月曆視圖 */}
      {activeTab === 'calendar' && (
        <div className="grid md:grid-cols-3 gap-4">
          {/* 月曆 */}
          <div className="md:col-span-2">
            {/* 月份導航 */}
            <div className="flex items-center justify-between mb-4">
              <button
                onClick={() => navigateMonth(-1)}
                className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors"
              >
                ◀
              </button>
              <h3 className="text-lg font-medium text-white">
                {currentDate.getFullYear()} 年 {currentDate.getMonth() + 1} 月
              </h3>
              <button
                onClick={() => navigateMonth(1)}
                className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors"
              >
                ▶
              </button>
            </div>

            {/* 星期標題 */}
            <div className="grid grid-cols-7 gap-0 mb-1">
              {['日', '一', '二', '三', '四', '五', '六'].map((day, i) => (
                <div
                  key={day}
                  className={`text-center py-2 text-sm font-medium ${
                    i === 0 || i === 6 ? 'text-slate-500' : 'text-slate-400'
                  }`}
                >
                  {day}
                </div>
              ))}
            </div>

            {/* 日曆網格 */}
            <div className="grid grid-cols-7 gap-0">{getCalendarDays.map(renderCalendarCell)}</div>

            {/* 圖例 */}
            <div className="flex flex-wrap gap-3 mt-4 pt-4 border-t border-slate-700">
              {Object.entries(EVENT_ICONS).map(([type, icon]) => (
                <div key={type} className="flex items-center gap-1 text-xs text-slate-400">
                  <span>{icon}</span>
                  <span>
                    {type === 'earnings' && '財報'}
                    {type === 'dividend' && '除息'}
                    {type === 'economic' && '經濟'}
                    {type === 'holiday_tw' && '台股休市'}
                    {type === 'holiday_us' && '美股休市'}
                    {type === 'custom' && '自訂'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 事件列表 */}
          <div>{renderEventList()}</div>
        </div>
      )}

      {/* 即將到來 */}
      {activeTab === 'upcoming' && (
        <div className="space-y-2">
          {upcomingEvents.length === 0 ? (
            <div className="text-center text-slate-500 py-8">近期沒有事件</div>
          ) : (
            upcomingEvents.map((event) => {
              const daysUntil = Math.ceil(
                (new Date(event.date) - new Date()) / (1000 * 60 * 60 * 24)
              );
              return (
                <div
                  key={event.id}
                  className={`flex items-center justify-between p-4 rounded-lg border ${EVENT_COLORS[event.type]}`}
                >
                  <div className="flex items-center gap-4">
                    <span className="text-2xl">{EVENT_ICONS[event.type]}</span>
                    <div>
                      <div className="text-white font-medium">{event.title}</div>
                      <div className="text-sm opacity-70">{event.date}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div
                      className={`text-lg font-bold ${
                        daysUntil <= 3 ? 'text-red-400' : daysUntil <= 7 ? 'text-yellow-400' : 'text-slate-400'
                      }`}
                    >
                      {daysUntil === 0 ? '今天' : daysUntil === 1 ? '明天' : `${daysUntil} 天後`}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* 休市總覽 */}
      {activeTab === 'holidays' && renderHolidayOverview()}

      {/* 新增事件 Modal */}
      {showEventModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md border border-slate-700">
            <h3 className="text-lg font-bold text-white mb-4">新增提醒</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-slate-400 text-sm mb-1">標題</label>
                <input
                  type="text"
                  value={newEvent.title}
                  onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如：台積電法說會"
                />
              </div>

              <div>
                <label className="block text-slate-400 text-sm mb-1">日期</label>
                <input
                  type="date"
                  value={newEvent.date}
                  onChange={(e) => setNewEvent({ ...newEvent, date: e.target.value })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowEventModal(false)}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleAddEvent}
                disabled={!newEvent.title || !newEvent.date}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                新增
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketCalendar;
