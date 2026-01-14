/**
 * KeyboardShortcuts.jsx - 鍵盤快捷鍵說明面板
 * V10.27 新增
 *
 * 功能：
 * - 顯示所有可用的鍵盤快捷鍵
 * - 分類顯示
 * - 按 ? 或 點擊按鈕開啟
 */

import React, { useState, useEffect } from 'react';
import { SHORTCUTS } from '../hooks/useKeyboardShortcuts';

// 將快捷鍵按類別分組
const groupShortcutsByCategory = () => {
  const groups = {};

  Object.entries(SHORTCUTS).forEach(([key, config]) => {
    const { category } = config;
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push({ key, ...config });
  });

  return groups;
};

// 快捷鍵說明面板
const KeyboardShortcutsModal = ({ isOpen, onClose }) => {
  const groups = groupShortcutsByCategory();

  // 按 Escape 關閉
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div
        className="bg-slate-800 rounded-xl border border-slate-700 max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 標題 */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>⌨️</span> 鍵盤快捷鍵
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {/* 內容 */}
        <div className="p-4 overflow-y-auto max-h-[60vh]">
          <div className="grid md:grid-cols-2 gap-6">
            {Object.entries(groups).map(([category, shortcuts]) => (
              <div key={category}>
                <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                  {category === '導航' && <span>🧭</span>}
                  {category === '動作' && <span>⚡</span>}
                  {category === '清單' && <span>📋</span>}
                  {category === '幫助' && <span>❓</span>}
                  {category}
                </h3>
                <div className="space-y-2">
                  {shortcuts.map(({ key, label }) => (
                    <div
                      key={key}
                      className="flex items-center justify-between py-2 px-3 bg-slate-700/50 rounded-lg"
                    >
                      <span className="text-slate-300">{label}</span>
                      <kbd className="px-2 py-1 bg-slate-900 border border-slate-600 rounded text-sm text-white font-mono">
                        {key}
                      </kbd>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* 提示 */}
          <div className="mt-6 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <div className="flex items-start gap-2">
              <span className="text-blue-400">💡</span>
              <div className="text-sm text-blue-400">
                <p className="mb-1">
                  <strong>組合鍵使用方式：</strong>先按第一個鍵（如 <kbd className="px-1 bg-slate-700 rounded">g</kbd>），再按第二個鍵（如 <kbd className="px-1 bg-slate-700 rounded">d</kbd>）
                </p>
                <p>
                  在輸入框中輸入時，大部分快捷鍵會被停用，按 <kbd className="px-1 bg-slate-700 rounded">Escape</kbd> 可離開輸入框
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 底部 */}
        <div className="p-4 border-t border-slate-700 bg-slate-800/50">
          <div className="text-center text-slate-500 text-sm">
            按 <kbd className="px-2 py-0.5 bg-slate-700 rounded">?</kbd> 開啟此說明，
            按 <kbd className="px-2 py-0.5 bg-slate-700 rounded">Esc</kbd> 關閉
          </div>
        </div>
      </div>
    </div>
  );
};

// 快捷鍵提示按鈕（顯示在畫面角落）
export const KeyboardShortcutsButton = ({ onClick }) => {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-4 right-4 p-3 bg-slate-700 hover:bg-slate-600 border border-slate-600 rounded-full shadow-lg text-white transition-all hover:scale-110 z-40"
      title="鍵盤快捷鍵 (?)"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
        />
      </svg>
    </button>
  );
};

// 快捷鍵指示器（顯示當前按鍵序列）
export const KeySequenceIndicator = ({ sequence }) => {
  if (!sequence) return null;

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg shadow-lg z-50">
      <div className="flex items-center gap-2 text-white">
        <span className="text-slate-400 text-sm">按鍵:</span>
        <kbd className="px-3 py-1 bg-blue-500 rounded font-mono text-lg">{sequence}</kbd>
        <span className="text-slate-500 text-sm">等待下一個鍵...</span>
      </div>
    </div>
  );
};

export default KeyboardShortcutsModal;
