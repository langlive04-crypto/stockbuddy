/**
 * MobileNav.jsx - V10.39 修改版（第 8 輪最終版）
 *
 * 手機端底部導航
 * - 底部固定 5 個主要入口（市場/AI/分析/投組/更多）
 * - 「更多」展開完整功能選單
 *
 * 安裝位置: 替換 stockbuddy-frontend/src/components/MobileNav.jsx
 */

import { useState, useEffect, memo } from 'react';
import PropTypes from 'prop-types';
import useResponsive from '../hooks/useResponsive';
import { menuGroups } from '../config/menuGroups';

const MobileNav = memo(({ activeSection, onNavigate }) => {
  const { isMobile } = useResponsive();
  const [showMore, setShowMore] = useState(false);

  // 點擊外部關閉
  useEffect(() => {
    if (showMore) {
      const handleClickOutside = (e) => {
        if (!e.target.closest('.mobile-nav-more-panel') &&
            !e.target.closest('.mobile-nav-more-btn')) {
          setShowMore(false);
        }
      };
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showMore]);

  if (!isMobile) return null;

  // 主要導航項目（底部固定顯示）
  const mainNavItems = [
    { id: 'dashboard', icon: '📊', label: '市場', groupId: 'market' },
    { id: 'ai', icon: '🎯', label: 'AI', groupId: 'ai-pick' },
    { id: 'search', icon: '🔍', label: '分析', groupId: 'analysis' },
    { id: 'portfolio', icon: '💼', label: '投組', groupId: 'portfolio' },
    { id: 'more', icon: '☰', label: '更多', isMore: true },
  ];

  // 「更多」選單中的項目（排除主導航中已有的群組）
  const moreGroups = menuGroups.filter(g =>
    !['market', 'ai-pick', 'analysis', 'portfolio'].includes(g.id)
  );

  // 判斷是否為活躍項目
  const isActive = (item) => {
    if (item.isMore) {
      // 如果當前 section 在「更多」群組中
      return moreGroups.some(group =>
        group.defaultSection === activeSection ||
        group.items.some(i => i.id === activeSection)
      );
    }

    // 檢查該項目所屬群組是否活躍
    const group = menuGroups.find(g => g.id === item.groupId);
    if (!group) return activeSection === item.id;

    return group.defaultSection === activeSection ||
      group.items.some(i => i.id === activeSection);
  };

  // 處理導航點擊
  const handleNavClick = (item) => {
    if (item.isMore) {
      setShowMore(!showMore);
    } else {
      onNavigate(item.id);
      setShowMore(false);
    }
  };

  // 處理「更多」選單中的項目點擊
  const handleMoreItemClick = (sectionId) => {
    onNavigate(sectionId);
    setShowMore(false);
  };

  return (
    <>
      {/* 遮罩層 */}
      {showMore && (
        <div
          className="fixed inset-0 bg-black/50 z-40 backdrop-blur-sm"
          onClick={() => setShowMore(false)}
        />
      )}

      {/* 更多選單面板 */}
      {showMore && (
        <div className="mobile-nav-more-panel fixed bottom-16 left-0 right-0 z-50
          bg-slate-900 border-t border-slate-700 rounded-t-2xl shadow-2xl
          max-h-[60vh] overflow-y-auto animate-slide-up">

          {/* 面板標題 */}
          <div className="sticky top-0 bg-slate-900 px-4 py-3 border-b border-slate-800 flex justify-between items-center">
            <span className="text-white font-medium">更多功能</span>
            <button
              onClick={() => setShowMore(false)}
              className="text-slate-400 hover:text-white p-1"
            >
              ✕
            </button>
          </div>

          {/* 功能列表 */}
          <div className="p-4 space-y-4">
            {moreGroups.map(group => (
              <div key={group.id}>
                {/* 群組標題 */}
                <div className="text-xs text-slate-500 font-medium mb-2 px-1">
                  {group.label}
                </div>

                {/* 群組項目 */}
                <div className="grid grid-cols-3 gap-2">
                  {group.items.length > 0 ? (
                    group.items.map(item => (
                      <button
                        key={item.id}
                        onClick={() => handleMoreItemClick(item.id)}
                        className={`
                          p-3 rounded-xl text-center transition-all
                          ${activeSection === item.id
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                          }
                        `}
                      >
                        <div className="text-xl mb-1">{item.icon}</div>
                        <div className="text-xs truncate">{item.label}</div>
                      </button>
                    ))
                  ) : (
                    // 無子選單的群組（如績效、提醒、美股）
                    <button
                      onClick={() => handleMoreItemClick(group.defaultSection)}
                      className={`
                        p-3 rounded-xl text-center transition-all col-span-1
                        ${activeSection === group.defaultSection
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        }
                      `}
                    >
                      <div className="text-xl mb-1">{group.label.split(' ')[0]}</div>
                      <div className="text-xs truncate">{group.label.split(' ').slice(1).join('')}</div>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 底部導航列 */}
      <nav className="fixed bottom-0 left-0 right-0 z-50
        bg-slate-900/95 backdrop-blur-md border-t border-slate-700
        px-2 py-1 safe-area-bottom">
        <div className="flex justify-around items-center max-w-lg mx-auto">
          {mainNavItems.map(item => (
            <button
              key={item.id}
              onClick={() => handleNavClick(item)}
              className={`
                mobile-nav-more-btn
                flex flex-col items-center justify-center
                py-2 px-4 rounded-xl min-w-[56px]
                transition-all duration-200 relative
                ${isActive(item)
                  ? 'text-blue-400'
                  : 'text-slate-400 hover:text-slate-200'
                }
              `}
            >
              <span className={`
                text-xl mb-0.5 transition-transform duration-200
                ${isActive(item) ? 'scale-110' : ''}
              `}>
                {item.icon}
              </span>
              <span className="text-[10px] font-medium">{item.label}</span>

              {/* 活躍指示器 */}
              {isActive(item) && !item.isMore && (
                <span className="absolute -bottom-1 left-1/2 -translate-x-1/2
                  w-6 h-0.5 bg-blue-500 rounded-full" />
              )}
            </button>
          ))}
        </div>
      </nav>

      {/* 底部安全區域佔位 */}
      <div className="h-16 md:hidden" />
    </>
  );
});

MobileNav.propTypes = {
  /** 當前選中的 section ID */
  activeSection: PropTypes.string,
  /** 導航切換時的回調函數 */
  onNavigate: PropTypes.func.isRequired,
};

MobileNav.defaultProps = {
  activeSection: 'dashboard',
};

export default MobileNav;
