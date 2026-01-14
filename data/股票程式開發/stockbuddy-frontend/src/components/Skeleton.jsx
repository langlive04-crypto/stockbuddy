/**
 * Skeleton.jsx - 載入骨架屏組件
 * V10.29 新增
 *
 * 功能：
 * - 內容載入佔位符
 * - 多種預設樣式
 * - 動畫效果
 * - 改善載入體驗
 */

import React, { memo } from 'react';

// 基礎骨架元素
export const SkeletonBase = memo(({ className = '', animate = true }) => (
  <div
    className={`bg-slate-700/50 rounded ${animate ? 'animate-pulse' : ''} ${className}`}
  />
));

// 文字骨架
export const SkeletonText = memo(({ lines = 1, className = '' }) => (
  <div className={`space-y-2 ${className}`}>
    {Array.from({ length: lines }).map((_, i) => (
      <SkeletonBase
        key={i}
        className={`h-4 ${i === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full'}`}
      />
    ))}
  </div>
));

// 標題骨架
export const SkeletonTitle = memo(({ className = '' }) => (
  <SkeletonBase className={`h-6 w-1/2 ${className}`} />
));

// 圓形骨架（頭像）
export const SkeletonCircle = memo(({ size = 'md', className = '' }) => {
  const sizeClass = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  }[size] || 'w-12 h-12';

  return <SkeletonBase className={`${sizeClass} rounded-full ${className}`} />;
});

// 按鈕骨架
export const SkeletonButton = memo(({ className = '' }) => (
  <SkeletonBase className={`h-10 w-24 rounded-lg ${className}`} />
));

// 股票卡片骨架
export const SkeletonStockCard = memo(() => (
  <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
    <div className="flex items-start justify-between mb-3">
      <div className="space-y-2">
        <SkeletonBase className="h-5 w-20" />
        <SkeletonBase className="h-4 w-16" />
      </div>
      <SkeletonBase className="h-8 w-16 rounded-lg" />
    </div>
    <div className="space-y-2">
      <div className="flex justify-between">
        <SkeletonBase className="h-4 w-12" />
        <SkeletonBase className="h-4 w-16" />
      </div>
      <div className="flex justify-between">
        <SkeletonBase className="h-4 w-14" />
        <SkeletonBase className="h-4 w-12" />
      </div>
    </div>
    <div className="mt-3 pt-3 border-t border-slate-700">
      <SkeletonBase className="h-3 w-full" />
    </div>
  </div>
));

// 股票列表骨架
export const SkeletonStockList = memo(({ count = 6 }) => (
  <div className="grid md:grid-cols-2 gap-3">
    {Array.from({ length: count }).map((_, i) => (
      <SkeletonStockCard key={i} />
    ))}
  </div>
));

// 分析面板骨架
export const SkeletonAnalysisPanel = memo(() => (
  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 space-y-4">
    <div className="flex items-center justify-between">
      <SkeletonTitle />
      <SkeletonBase className="h-8 w-8 rounded-lg" />
    </div>
    <div className="grid grid-cols-2 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="space-y-2">
          <SkeletonBase className="h-3 w-16" />
          <SkeletonBase className="h-6 w-20" />
        </div>
      ))}
    </div>
    <SkeletonBase className="h-32 w-full rounded-lg" />
    <SkeletonText lines={3} />
  </div>
));

// 圖表骨架
export const SkeletonChart = memo(({ height = 200, className = '' }) => (
  <div className={`relative ${className}`}>
    <SkeletonBase className={`w-full rounded-lg`} style={{ height }} />
    <div className="absolute inset-0 flex items-center justify-center">
      <div className="text-slate-500 text-sm">載入中...</div>
    </div>
  </div>
));

// 表格骨架
export const SkeletonTable = memo(({ rows = 5, cols = 4 }) => (
  <div className="space-y-2">
    {/* 表頭 */}
    <div className="flex gap-4 pb-2 border-b border-slate-700">
      {Array.from({ length: cols }).map((_, i) => (
        <SkeletonBase key={i} className="h-4 flex-1" />
      ))}
    </div>
    {/* 表格行 */}
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <div key={rowIndex} className="flex gap-4 py-2">
        {Array.from({ length: cols }).map((_, colIndex) => (
          <SkeletonBase key={colIndex} className="h-4 flex-1" />
        ))}
      </div>
    ))}
  </div>
));

// 儀表板骨架
export const SkeletonDashboard = memo(() => (
  <div className="space-y-6">
    {/* 頂部統計卡片 */}
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <SkeletonBase className="h-3 w-16 mb-2" />
          <SkeletonBase className="h-8 w-24" />
        </div>
      ))}
    </div>
    {/* 主要內容 */}
    <div className="grid lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <SkeletonChart height={300} />
      </div>
      <div>
        <SkeletonAnalysisPanel />
      </div>
    </div>
  </div>
));

// 通用骨架包裝器
const Skeleton = ({
  type = 'text',
  loading = true,
  children,
  ...props
}) => {
  if (!loading) return children;

  const components = {
    text: SkeletonText,
    title: SkeletonTitle,
    circle: SkeletonCircle,
    button: SkeletonButton,
    card: SkeletonStockCard,
    list: SkeletonStockList,
    analysis: SkeletonAnalysisPanel,
    chart: SkeletonChart,
    table: SkeletonTable,
    dashboard: SkeletonDashboard,
  };

  const Component = components[type] || SkeletonBase;
  return <Component {...props} />;
};

export default Skeleton;
