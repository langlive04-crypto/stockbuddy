/**
 * useKeyboardShortcuts.js - 鍵盤快捷鍵 Hook
 * V10.27 新增
 *
 * 功能：
 * - 全域鍵盤快捷鍵監聽
 * - Tab 切換快捷鍵
 * - 搜尋快捷鍵
 * - 刷新快捷鍵
 */

import { useEffect, useCallback, useState } from 'react';

// 快捷鍵配置
export const SHORTCUTS = {
  // 導航
  'g d': { action: 'goto_dashboard', label: '前往市場總覽', category: '導航' },
  'g a': { action: 'goto_ai', label: '前往 AI 精選', category: '導航' },
  'g s': { action: 'goto_screener', label: '前往選股篩選', category: '導航' },
  'g u': { action: 'goto_us', label: '前往美股市場', category: '導航' },
  'g c': { action: 'goto_calendar', label: '前往市場行事曆', category: '導航' },
  'g p': { action: 'goto_portfolio', label: '前往我的投組', category: '導航' },

  // 動作
  '/': { action: 'focus_search', label: '聚焦搜尋框', category: '動作' },
  'r': { action: 'refresh', label: '刷新資料', category: '動作' },
  'e': { action: 'export', label: '匯出資料', category: '動作' },
  't': { action: 'toggle_theme', label: '切換主題', category: '動作' },

  // 清單操作
  'j': { action: 'next_item', label: '下一項', category: '清單' },
  'k': { action: 'prev_item', label: '上一項', category: '清單' },
  'Enter': { action: 'select_item', label: '選擇項目', category: '清單' },
  'Escape': { action: 'close_modal', label: '關閉視窗', category: '清單' },

  // 幫助
  '?': { action: 'show_help', label: '顯示快捷鍵說明', category: '幫助' },
};

// 將 Tab ID 對應到快捷鍵動作
const TAB_MAPPING = {
  goto_dashboard: 'dashboard',
  goto_ai: 'ai',
  goto_screener: 'screener',
  goto_us: 'us-stocks',
  goto_calendar: 'calendar',
  goto_portfolio: 'portfolio',
};

const useKeyboardShortcuts = ({
  onNavigate,
  onRefresh,
  onExport,
  onToggleTheme,
  onShowHelp,
  onCloseModal,
  onNextItem,
  onPrevItem,
  onSelectItem,
  enabled = true,
}) => {
  const [keySequence, setKeySequence] = useState('');
  const [lastKeyTime, setLastKeyTime] = useState(0);

  const handleKeyDown = useCallback(
    (event) => {
      if (!enabled) return;

      // 如果在輸入框中，忽略大部分快捷鍵
      const isInputActive =
        event.target.tagName === 'INPUT' ||
        event.target.tagName === 'TEXTAREA' ||
        event.target.isContentEditable;

      // 允許的特殊鍵（在輸入框中也可用）
      const allowedInInput = ['Escape'];

      if (isInputActive && !allowedInInput.includes(event.key)) {
        // 只有 '/' 可以在非輸入框狀態下觸發聚焦搜尋
        if (event.key === '/' && !isInputActive) {
          event.preventDefault();
          // Focus search will be handled below
        } else {
          return;
        }
      }

      const now = Date.now();
      const key = event.key;

      // 處理組合鍵序列（如 'g d'）
      if (now - lastKeyTime < 500) {
        const newSequence = `${keySequence} ${key}`.trim();
        setKeySequence(newSequence);
        setLastKeyTime(now);

        // 檢查是否匹配快捷鍵
        if (SHORTCUTS[newSequence]) {
          event.preventDefault();
          executeAction(SHORTCUTS[newSequence].action);
          setKeySequence('');
          return;
        }
      } else {
        setKeySequence(key);
        setLastKeyTime(now);

        // 檢查單鍵快捷鍵
        if (SHORTCUTS[key]) {
          // 跳過需要組合的鍵（如 'g'）
          if (key === 'g') return;

          event.preventDefault();
          executeAction(SHORTCUTS[key].action);
          setKeySequence('');
          return;
        }
      }
    },
    [enabled, keySequence, lastKeyTime]
  );

  const executeAction = useCallback(
    (action) => {
      // 導航動作
      if (TAB_MAPPING[action] && onNavigate) {
        onNavigate(TAB_MAPPING[action]);
        return;
      }

      // 其他動作
      switch (action) {
        case 'focus_search':
          const searchInput = document.querySelector('input[type="text"][placeholder*="搜尋"]');
          if (searchInput) {
            searchInput.focus();
          }
          break;
        case 'refresh':
          onRefresh?.();
          break;
        case 'export':
          onExport?.();
          break;
        case 'toggle_theme':
          onToggleTheme?.();
          break;
        case 'show_help':
          onShowHelp?.();
          break;
        case 'close_modal':
          onCloseModal?.();
          break;
        case 'next_item':
          onNextItem?.();
          break;
        case 'prev_item':
          onPrevItem?.();
          break;
        case 'select_item':
          onSelectItem?.();
          break;
        default:
          break;
      }
    },
    [onNavigate, onRefresh, onExport, onToggleTheme, onShowHelp, onCloseModal, onNextItem, onPrevItem, onSelectItem]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  // 清除過期的鍵序列
  useEffect(() => {
    const timer = setTimeout(() => {
      if (keySequence && Date.now() - lastKeyTime > 500) {
        setKeySequence('');
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [keySequence, lastKeyTime]);

  return {
    keySequence,
    shortcuts: SHORTCUTS,
  };
};

export default useKeyboardShortcuts;
