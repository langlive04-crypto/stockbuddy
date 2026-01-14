/**
 * StockBuddy V10.21 - 自選股分類群組組件
 * 提供自選股分類管理功能
 *
 * 功能：
 * - 建立/編輯/刪除分類群組
 * - 股票加入/移除群組
 * - 分類統計圖表
 * - 智能分類建議
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { API_BASE } from '../config';

// localStorage keys
const CATEGORIES_KEY = 'stockbuddy_watchlist_categories';
const CATEGORY_STOCKS_KEY = 'stockbuddy_category_stocks';

// 顏色配置（與後端同步）
const COLOR_PALETTE = {
  red: { bg: '#fef2f2', border: '#fecaca', text: '#ef4444', dark: '#7f1d1d' },
  orange: { bg: '#fff7ed', border: '#fed7aa', text: '#f97316', dark: '#7c2d12' },
  yellow: { bg: '#fefce8', border: '#fef08a', text: '#eab308', dark: '#713f12' },
  green: { bg: '#f0fdf4', border: '#bbf7d0', text: '#22c55e', dark: '#14532d' },
  teal: { bg: '#f0fdfa', border: '#99f6e4', text: '#14b8a6', dark: '#134e4a' },
  blue: { bg: '#eff6ff', border: '#bfdbfe', text: '#3b82f6', dark: '#1e3a8a' },
  indigo: { bg: '#eef2ff', border: '#c7d2fe', text: '#6366f1', dark: '#312e81' },
  purple: { bg: '#faf5ff', border: '#e9d5ff', text: '#a855f7', dark: '#581c87' },
  pink: { bg: '#fdf2f8', border: '#fbcfe8', text: '#ec4899', dark: '#831843' },
  gray: { bg: '#f9fafb', border: '#e5e7eb', text: '#6b7280', dark: '#1f2937' },
};

export default function WatchlistCategories({ trackedStocks = [], onSelectStock }) {
  // 分類列表
  const [categories, setCategories] = useState([]);

  // 股票分類對應 { categoryId: [stockIds] }
  const [categoryStocks, setCategoryStocks] = useState({});

  // 預設分類模板
  const [defaultCategories, setDefaultCategories] = useState([]);

  // 可用顏色
  const [availableColors, setAvailableColors] = useState([]);

  // 可用圖示
  const [availableIcons, setAvailableIcons] = useState([]);

  // 分類統計
  const [stats, setStats] = useState(null);

  // UI 狀態
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [activeCategory, setActiveCategory] = useState(null);
  const [showAssign, setShowAssign] = useState(false);

  // 表單狀態
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    color: 'blue',
    icon: '📈',
  });

  // 載入分類資料
  useEffect(() => {
    // 從 localStorage 載入
    const savedCategories = localStorage.getItem(CATEGORIES_KEY);
    const savedStocks = localStorage.getItem(CATEGORY_STOCKS_KEY);

    if (savedCategories) {
      try {
        setCategories(JSON.parse(savedCategories));
      } catch (e) {
        console.error('載入分類失敗:', e);
      }
    }

    if (savedStocks) {
      try {
        setCategoryStocks(JSON.parse(savedStocks));
      } catch (e) {
        console.error('載入分類股票失敗:', e);
      }
    }

    // 載入預設模板和配置
    loadConfigurations();
  }, []);

  // 載入配置
  const loadConfigurations = async () => {
    try {
      const [defaultsRes, colorsRes, iconsRes] = await Promise.all([
        fetch(`${API_BASE}/api/stocks/categories/defaults`),
        fetch(`${API_BASE}/api/stocks/categories/colors`),
        fetch(`${API_BASE}/api/stocks/categories/icons`),
      ]);

      const defaults = await defaultsRes.json();
      const colors = await colorsRes.json();
      const icons = await iconsRes.json();

      if (defaults.success) setDefaultCategories(defaults.categories);
      if (colors.success) setAvailableColors(colors.colors);
      if (icons.success) setAvailableIcons(icons.icons);
    } catch (error) {
      console.error('載入配置失敗:', error);
    }
  };

  // 儲存分類
  useEffect(() => {
    localStorage.setItem(CATEGORIES_KEY, JSON.stringify(categories));
  }, [categories]);

  // 儲存股票分類對應
  useEffect(() => {
    localStorage.setItem(CATEGORY_STOCKS_KEY, JSON.stringify(categoryStocks));
  }, [categoryStocks]);

  // 分析統計
  const analyzeStats = useCallback(async () => {
    if (categories.length === 0) {
      setStats(null);
      return;
    }

    try {
      // 構建請求資料
      const stocksByCategory = {};
      for (const catId of Object.keys(categoryStocks)) {
        stocksByCategory[catId] = (categoryStocks[catId] || []).map(sid => ({ stock_id: sid }));
      }

      const res = await fetch(`${API_BASE}/api/stocks/categories/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          categories,
          stocks_by_category: stocksByCategory,
        }),
      });

      const data = await res.json();
      if (data.success) {
        setStats(data);
      }
    } catch (error) {
      console.error('分析統計失敗:', error);
    }
  }, [categories, categoryStocks]);

  // 分類變更時重新分析
  useEffect(() => {
    analyzeStats();
  }, [categories, categoryStocks, analyzeStats]);

  // 使用預設模板初始化
  const initWithDefaults = () => {
    if (categories.length > 0) {
      if (!window.confirm('這會覆蓋現有分類，確定要初始化嗎？')) {
        return;
      }
    }
    setCategories(defaultCategories.map(cat => ({
      ...cat,
      id: cat.id || `cat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    })));
    setCategoryStocks({});
  };

  // 新增/編輯分類
  const handleSubmit = (e) => {
    e.preventDefault();

    const newCategory = {
      id: editingId || `cat_${Date.now()}`,
      name: formData.name.trim(),
      description: formData.description.trim(),
      color: formData.color,
      icon: formData.icon,
    };

    if (editingId) {
      setCategories(prev => prev.map(c => c.id === editingId ? newCategory : c));
    } else {
      setCategories(prev => [...prev, newCategory]);
    }

    resetForm();
  };

  // 重設表單
  const resetForm = () => {
    setFormData({ name: '', description: '', color: 'blue', icon: '📈' });
    setShowForm(false);
    setEditingId(null);
  };

  // 編輯分類
  const handleEdit = (cat) => {
    setFormData({
      name: cat.name,
      description: cat.description || '',
      color: cat.color,
      icon: cat.icon,
    });
    setEditingId(cat.id);
    setShowForm(true);
  };

  // 刪除分類
  const handleDelete = (id) => {
    if (window.confirm('確定要刪除這個分類嗎？分類內的股票不會被刪除。')) {
      setCategories(prev => prev.filter(c => c.id !== id));
      setCategoryStocks(prev => {
        const newStocks = { ...prev };
        delete newStocks[id];
        return newStocks;
      });
      if (activeCategory === id) {
        setActiveCategory(null);
      }
    }
  };

  // 分配股票到分類
  const assignStock = (stockId, categoryId) => {
    setCategoryStocks(prev => {
      const newStocks = { ...prev };

      // 先從所有分類移除
      for (const catId of Object.keys(newStocks)) {
        newStocks[catId] = (newStocks[catId] || []).filter(s => s !== stockId);
      }

      // 加入新分類
      if (categoryId) {
        if (!newStocks[categoryId]) {
          newStocks[categoryId] = [];
        }
        newStocks[categoryId].push(stockId);
      }

      return newStocks;
    });
  };

  // 取得股票所屬分類
  const getStockCategory = (stockId) => {
    for (const [catId, stocks] of Object.entries(categoryStocks)) {
      if (stocks.includes(stockId)) {
        return catId;
      }
    }
    return null;
  };

  // 取得分類的股票列表
  const getCategoryStocks = (categoryId) => {
    const stockIds = categoryStocks[categoryId] || [];
    return trackedStocks.filter(s => stockIds.includes(s.stock_id));
  };

  // 未分類的股票
  const uncategorizedStocks = useMemo(() => {
    const allCategorized = new Set(Object.values(categoryStocks).flat());
    return trackedStocks.filter(s => !allCategorized.has(s.stock_id));
  }, [trackedStocks, categoryStocks]);

  return (
    <div style={{
      backgroundColor: '#1a1a2e',
      borderRadius: 12,
      padding: 20,
      minHeight: 400,
    }}>
      {/* 標題列 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
      }}>
        <h2 style={{ margin: 0, fontSize: 20, color: '#fff' }}>
          📁 自選股分類
        </h2>
        <div style={{ display: 'flex', gap: 8 }}>
          {categories.length === 0 && (
            <button
              onClick={initWithDefaults}
              style={{
                padding: '8px 16px',
                backgroundColor: '#2d2d44',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                cursor: 'pointer',
              }}
            >
              使用預設模板
            </button>
          )}
          <button
            onClick={() => setShowForm(true)}
            style={{
              padding: '8px 16px',
              background: 'linear-gradient(135deg, #10b981, #14b8a6)',
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            + 新增分類
          </button>
        </div>
      </div>

      {/* 統計概覽 */}
      {stats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
          gap: 12,
          marginBottom: 20,
        }}>
          <div style={{
            backgroundColor: '#2d2d44',
            padding: 12,
            borderRadius: 8,
            textAlign: 'center',
          }}>
            <div style={{ color: '#888', fontSize: 12 }}>分類數</div>
            <div style={{ color: '#fff', fontSize: 20, fontWeight: 600 }}>
              {stats.total_categories}
            </div>
          </div>
          <div style={{
            backgroundColor: '#2d2d44',
            padding: 12,
            borderRadius: 8,
            textAlign: 'center',
          }}>
            <div style={{ color: '#888', fontSize: 12 }}>已分類</div>
            <div style={{ color: '#fff', fontSize: 20, fontWeight: 600 }}>
              {stats.total_stocks}
            </div>
          </div>
          <div style={{
            backgroundColor: '#2d2d44',
            padding: 12,
            borderRadius: 8,
            textAlign: 'center',
          }}>
            <div style={{ color: '#888', fontSize: 12 }}>未分類</div>
            <div style={{ color: '#fff', fontSize: 20, fontWeight: 600 }}>
              {uncategorizedStocks.length}
            </div>
          </div>
        </div>
      )}

      {/* 分類列表 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {categories.map(cat => {
          const colorConfig = COLOR_PALETTE[cat.color] || COLOR_PALETTE.gray;
          const stocks = getCategoryStocks(cat.id);
          const isActive = activeCategory === cat.id;

          return (
            <div
              key={cat.id}
              style={{
                backgroundColor: '#2d2d44',
                borderRadius: 8,
                overflow: 'hidden',
                border: isActive ? `2px solid ${colorConfig.text}` : '2px solid transparent',
              }}
            >
              {/* 分類標題 */}
              <div
                onClick={() => setActiveCategory(isActive ? null : cat.id)}
                style={{
                  padding: 16,
                  cursor: 'pointer',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  transition: 'background 0.2s',
                }}
                onMouseOver={e => e.currentTarget.style.backgroundColor = '#3d3d54'}
                onMouseOut={e => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{
                    width: 36,
                    height: 36,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: colorConfig.text + '20',
                    borderRadius: 8,
                    fontSize: 18,
                  }}>
                    {cat.icon}
                  </span>
                  <div>
                    <div style={{ color: '#fff', fontWeight: 600 }}>{cat.name}</div>
                    {cat.description && (
                      <div style={{ color: '#888', fontSize: 12 }}>{cat.description}</div>
                    )}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{
                    padding: '4px 12px',
                    backgroundColor: colorConfig.text + '20',
                    color: colorConfig.text,
                    borderRadius: 20,
                    fontSize: 14,
                    fontWeight: 600,
                  }}>
                    {stocks.length} 檔
                  </span>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleEdit(cat); }}
                    style={{
                      padding: '4px 8px',
                      backgroundColor: '#4d4d64',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 4,
                      cursor: 'pointer',
                      fontSize: 12,
                    }}
                  >
                    編輯
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(cat.id); }}
                    style={{
                      padding: '4px 8px',
                      backgroundColor: '#ef4444',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 4,
                      cursor: 'pointer',
                      fontSize: 12,
                    }}
                  >
                    刪除
                  </button>
                </div>
              </div>

              {/* 分類內股票 */}
              {isActive && (
                <div style={{
                  padding: '0 16px 16px',
                  borderTop: '1px solid #3d3d54',
                }}>
                  {stocks.length > 0 ? (
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
                      gap: 8,
                      marginTop: 12,
                    }}>
                      {stocks.map(stock => (
                        <div
                          key={stock.stock_id}
                          onClick={() => onSelectStock?.(stock.stock_id)}
                          style={{
                            padding: 12,
                            backgroundColor: '#1a1a2e',
                            borderRadius: 6,
                            cursor: 'pointer',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                          }}
                        >
                          <div>
                            <div style={{ color: '#fff', fontSize: 14 }}>{stock.name}</div>
                            <div style={{ color: '#888', fontSize: 12 }}>{stock.stock_id}</div>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              assignStock(stock.stock_id, null);
                            }}
                            style={{
                              padding: '2px 6px',
                              backgroundColor: 'transparent',
                              color: '#888',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: 12,
                            }}
                          >
                            移除
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: 20, color: '#888' }}>
                      尚無股票，從下方未分類區域拖曳或點擊加入
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {categories.length === 0 && (
          <div style={{ textAlign: 'center', padding: 40, color: '#888' }}>
            尚無分類，點擊「使用預設模板」快速開始或「新增分類」自訂
          </div>
        )}
      </div>

      {/* 未分類股票 */}
      {uncategorizedStocks.length > 0 && categories.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <h3 style={{ color: '#888', fontSize: 14, marginBottom: 12 }}>
            未分類股票 ({uncategorizedStocks.length})
          </h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
            gap: 8,
          }}>
            {uncategorizedStocks.map(stock => (
              <div
                key={stock.stock_id}
                style={{
                  padding: 12,
                  backgroundColor: '#2d2d44',
                  borderRadius: 8,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div
                  onClick={() => onSelectStock?.(stock.stock_id)}
                  style={{ cursor: 'pointer' }}
                >
                  <div style={{ color: '#fff', fontSize: 14 }}>{stock.name}</div>
                  <div style={{ color: '#888', fontSize: 12 }}>{stock.stock_id}</div>
                </div>
                <select
                  onChange={(e) => {
                    if (e.target.value) {
                      assignStock(stock.stock_id, e.target.value);
                    }
                  }}
                  style={{
                    padding: '4px 8px',
                    backgroundColor: '#1a1a2e',
                    color: '#fff',
                    border: '1px solid #3d3d54',
                    borderRadius: 4,
                    fontSize: 12,
                    cursor: 'pointer',
                  }}
                  defaultValue=""
                >
                  <option value="" disabled>分類</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon} {cat.name}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 新增/編輯表單 Modal */}
      {showForm && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => resetForm()}
        >
          <div
            style={{
              backgroundColor: '#1a1a2e',
              padding: 24,
              borderRadius: 12,
              width: '90%',
              maxWidth: 450,
            }}
            onClick={e => e.stopPropagation()}
          >
            <h3 style={{ margin: '0 0 20px 0', color: '#fff' }}>
              {editingId ? '編輯分類' : '新增分類'}
            </h3>

            <form onSubmit={handleSubmit}>
              {/* 名稱 */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ color: '#888', fontSize: 12 }}>分類名稱 *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="例：存股標的"
                  required
                  maxLength={20}
                  style={{
                    width: '100%',
                    padding: 10,
                    marginTop: 6,
                    backgroundColor: '#2d2d44',
                    color: '#fff',
                    border: '1px solid #3d3d54',
                    borderRadius: 6,
                  }}
                />
              </div>

              {/* 描述 */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ color: '#888', fontSize: 12 }}>描述</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="例：長期持有的穩定配息股"
                  maxLength={100}
                  style={{
                    width: '100%',
                    padding: 10,
                    marginTop: 6,
                    backgroundColor: '#2d2d44',
                    color: '#fff',
                    border: '1px solid #3d3d54',
                    borderRadius: 6,
                  }}
                />
              </div>

              {/* 顏色選擇 */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ color: '#888', fontSize: 12 }}>顏色</label>
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 8,
                  marginTop: 8,
                }}>
                  {Object.entries(COLOR_PALETTE).map(([color, config]) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, color }))}
                      style={{
                        width: 32,
                        height: 32,
                        backgroundColor: config.text,
                        border: formData.color === color ? '3px solid #fff' : 'none',
                        borderRadius: 6,
                        cursor: 'pointer',
                      }}
                    />
                  ))}
                </div>
              </div>

              {/* 圖示選擇 */}
              <div style={{ marginBottom: 20 }}>
                <label style={{ color: '#888', fontSize: 12 }}>圖示</label>
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 8,
                  marginTop: 8,
                }}>
                  {availableIcons.map(icon => (
                    <button
                      key={icon.value}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, icon: icon.value }))}
                      style={{
                        width: 36,
                        height: 36,
                        backgroundColor: formData.icon === icon.value ? '#3b82f6' : '#2d2d44',
                        border: 'none',
                        borderRadius: 6,
                        cursor: 'pointer',
                        fontSize: 18,
                      }}
                    >
                      {icon.value}
                    </button>
                  ))}
                </div>
              </div>

              {/* 預覽 */}
              <div style={{
                backgroundColor: '#2d2d44',
                padding: 12,
                borderRadius: 8,
                marginBottom: 20,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
              }}>
                <span style={{
                  width: 40,
                  height: 40,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: (COLOR_PALETTE[formData.color]?.text || '#3b82f6') + '20',
                  borderRadius: 8,
                  fontSize: 20,
                }}>
                  {formData.icon}
                </span>
                <div>
                  <div style={{ color: '#fff', fontWeight: 600 }}>
                    {formData.name || '分類名稱'}
                  </div>
                  <div style={{ color: '#888', fontSize: 12 }}>
                    {formData.description || '分類描述'}
                  </div>
                </div>
              </div>

              {/* 按鈕 */}
              <div style={{ display: 'flex', gap: 12 }}>
                <button
                  type="button"
                  onClick={resetForm}
                  style={{
                    flex: 1,
                    padding: 12,
                    backgroundColor: '#3d3d54',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 6,
                    cursor: 'pointer',
                  }}
                >
                  取消
                </button>
                <button
                  type="submit"
                  style={{
                    flex: 2,
                    padding: 12,
                    background: 'linear-gradient(135deg, #10b981, #14b8a6)',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 6,
                    cursor: 'pointer',
                    fontWeight: 600,
                  }}
                >
                  {editingId ? '更新' : '新增'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
