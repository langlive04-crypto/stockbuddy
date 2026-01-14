/**
 * DropdownMenu.jsx - V10.39 新增（第 8 輪最終版）
 *
 * 下拉選單元件，用於整合多個相關功能
 *
 * 安裝位置: stockbuddy-frontend/src/components/DropdownMenu.jsx
 *
 * 功能特點:
 * - 點擊外部自動關閉
 * - ESC 鍵關閉
 * - 完整鍵盤導航（上下箭頭選擇）
 * - ARIA 無障礙支援
 * - 效能優化（條件式事件監聽）
 *
 * 使用方式:
 * import DropdownMenu from './components/DropdownMenu';
 *
 * <DropdownMenu
 *   group={menuGroup}
 *   activeSection={activeSection}
 *   onSelect={setActiveSection}
 * />
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';

const DropdownMenu = ({
  group,
  activeSection,
  onSelect,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const dropdownRef = useRef(null);
  const menuItemsRef = useRef([]);

  const hasSubmenu = group.items && group.items.length > 0;
  const isActive = hasSubmenu
    ? group.items.some(item => item.id === activeSection)
    : group.defaultSection === activeSection;

  // 點擊外部關閉下拉選單
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
        setFocusedIndex(-1);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // 按 ESC 關閉（僅在開啟時監聽）
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
        setFocusedIndex(-1);
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  // 焦點管理
  useEffect(() => {
    if (isOpen && focusedIndex >= 0 && menuItemsRef.current[focusedIndex]) {
      menuItemsRef.current[focusedIndex].focus();
    }
  }, [isOpen, focusedIndex]);

  // 主按鈕點擊
  const handleMainClick = useCallback(() => {
    if (hasSubmenu) {
      setIsOpen(prev => !prev);
      setFocusedIndex(-1);
    } else {
      onSelect(group.defaultSection);
    }
  }, [hasSubmenu, onSelect, group.defaultSection]);

  // 子項目點擊
  const handleItemClick = useCallback((itemId) => {
    onSelect(itemId);
    setIsOpen(false);
    setFocusedIndex(-1);
  }, [onSelect]);

  // 主按鈕鍵盤事件
  const handleMainKeyDown = useCallback((event) => {
    if (!hasSubmenu) return;

    switch (event.key) {
      case 'Enter':
      case ' ':
        event.preventDefault();
        setIsOpen(prev => !prev);
        if (!isOpen) setFocusedIndex(0);
        break;
      case 'ArrowDown':
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(0);
        }
        break;
      case 'ArrowUp':
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(group.items.length - 1);
        }
        break;
      default:
        break;
    }
  }, [hasSubmenu, isOpen, group.items?.length]);

  // 選單項目鍵盤事件
  const handleItemKeyDown = useCallback((event, index) => {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        setFocusedIndex(prev =>
          prev < group.items.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        event.preventDefault();
        setFocusedIndex(prev =>
          prev > 0 ? prev - 1 : group.items.length - 1
        );
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        handleItemClick(group.items[index].id);
        break;
      case 'Tab':
        setIsOpen(false);
        setFocusedIndex(-1);
        break;
      default:
        break;
    }
  }, [group.items, handleItemClick]);

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      {/* 主選單按鈕 */}
      <button
        onClick={handleMainClick}
        onKeyDown={handleMainKeyDown}
        aria-expanded={hasSubmenu ? isOpen : undefined}
        aria-haspopup={hasSubmenu ? 'menu' : undefined}
        aria-label={`${group.label}${hasSubmenu ? ' 選單' : ''}`}
        className={`
          px-3 md:px-4 py-1.5 md:py-2 rounded-lg text-xs md:text-sm font-medium
          whitespace-nowrap transition-all duration-200 flex items-center gap-1
          touch-manipulation focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500
          ${isActive
            ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25'
            : 'bg-slate-700/50 text-slate-300 hover:bg-slate-600/50 hover:text-white'
          }
        `}
      >
        <span>{group.label}</span>
        {hasSubmenu && (
          <svg
            className={`w-3 h-3 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        )}
      </button>

      {/* 下拉選單 */}
      {hasSubmenu && isOpen && (
        <div
          className="
            absolute top-full left-0 mt-1 py-1 min-w-[180px]
            bg-slate-800 border border-slate-600 rounded-xl shadow-2xl z-50
            animate-dropdown
          "
          role="menu"
          aria-label={`${group.label} 子選單`}
        >
          {group.items.map((item, index) => (
            <button
              key={item.id}
              ref={el => menuItemsRef.current[index] = el}
              onClick={() => handleItemClick(item.id)}
              onKeyDown={(e) => handleItemKeyDown(e, index)}
              role="menuitem"
              tabIndex={focusedIndex === index ? 0 : -1}
              className={`
                w-full px-4 py-2.5 text-left text-sm flex items-center gap-2.5
                transition-colors duration-150 focus:outline-none
                ${activeSection === item.id
                  ? 'bg-blue-600/20 text-blue-400'
                  : 'text-slate-300 hover:bg-slate-700/50 hover:text-white focus:bg-slate-700/50 focus:text-white'
                }
                ${index === 0 ? 'rounded-t-lg' : ''}
                ${index === group.items.length - 1 ? 'rounded-b-lg' : ''}
              `}
            >
              <span className="text-base" aria-hidden="true">{item.icon}</span>
              <span className="flex-1">{item.label}</span>
              {activeSection === item.id && (
                <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

DropdownMenu.propTypes = {
  /** 選單群組配置物件 */
  group: PropTypes.shape({
    id: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,
    defaultSection: PropTypes.string.isRequired,
    items: PropTypes.arrayOf(PropTypes.shape({
      id: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
      icon: PropTypes.string,
    })),
  }).isRequired,
  /** 當前選中的 section ID */
  activeSection: PropTypes.string,
  /** 選擇項目時的回調函數 */
  onSelect: PropTypes.func.isRequired,
  /** 額外的 CSS 類名 */
  className: PropTypes.string,
};

DropdownMenu.defaultProps = {
  activeSection: '',
  className: '',
};

export default DropdownMenu;
