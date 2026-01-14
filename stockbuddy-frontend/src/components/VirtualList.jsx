/**
 * VirtualList - 虛擬滾動列表組件 V10.38
 *
 * 使用 react-window 實現高效能的長列表渲染
 * 只渲染可視區域內的項目，大幅提升效能
 *
 * 使用範例:
 * <VirtualList
 *   items={stocks}
 *   itemHeight={80}
 *   renderItem={({ item, index, style }) => (
 *     <div style={style}>
 *       {item.name}
 *     </div>
 *   )}
 * />
 */

import { useRef, useCallback, memo, forwardRef } from 'react';
import { FixedSizeList, VariableSizeList } from 'react-window';
import PropTypes from 'prop-types';

/**
 * 股票列表項目組件
 */
const StockListItem = memo(({ data, index, style }) => {
  const { items, renderItem, onItemClick } = data;
  const item = items[index];

  if (!item) return null;

  return (
    <div
      style={style}
      onClick={() => onItemClick?.(item, index)}
      className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
    >
      {renderItem({ item, index, style: {} })}
    </div>
  );
});

StockListItem.displayName = 'StockListItem';

StockListItem.propTypes = {
  data: PropTypes.shape({
    items: PropTypes.array.isRequired,
    renderItem: PropTypes.func.isRequired,
    onItemClick: PropTypes.func,
  }).isRequired,
  index: PropTypes.number.isRequired,
  style: PropTypes.object.isRequired,
};

/**
 * 虛擬滾動列表
 */
const VirtualList = forwardRef(({
  items,
  itemHeight = 60,
  height = 400,
  width = '100%',
  renderItem,
  onItemClick,
  className = '',
  overscanCount = 5,
  variableSize = false,
  getItemSize,
  emptyMessage = '沒有資料',
  loadingMessage = '載入中...',
  isLoading = false,
}, ref) => {
  const listRef = useRef(null);

  // 計算項目高度（用於 VariableSizeList）
  const getSize = useCallback((index) => {
    if (getItemSize) {
      return getItemSize(items[index], index);
    }
    return itemHeight;
  }, [items, itemHeight, getItemSize]);

  // 捲動到指定項目
  const scrollToItem = useCallback((index, align = 'auto') => {
    if (listRef.current) {
      listRef.current.scrollToItem(index, align);
    }
  }, []);

  // 暴露給父組件的方法
  if (ref) {
    ref.current = {
      scrollToItem,
      scrollToTop: () => scrollToItem(0),
      scrollToBottom: () => scrollToItem(items.length - 1),
    };
  }

  // 載入中狀態
  if (isLoading) {
    return (
      <div
        className={`flex items-center justify-center text-gray-500 dark:text-gray-400 ${className}`}
        style={{ height, width }}
      >
        <div className="flex items-center space-x-2">
          <svg
            className="animate-spin h-5 w-5"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <span>{loadingMessage}</span>
        </div>
      </div>
    );
  }

  // 空狀態
  if (!items || items.length === 0) {
    return (
      <div
        className={`flex items-center justify-center text-gray-500 dark:text-gray-400 ${className}`}
        style={{ height, width }}
      >
        <span>{emptyMessage}</span>
      </div>
    );
  }

  // 共用數據
  const itemData = {
    items,
    renderItem,
    onItemClick,
  };

  // 使用 VariableSizeList 或 FixedSizeList
  const ListComponent = variableSize ? VariableSizeList : FixedSizeList;
  const listProps = variableSize
    ? { itemSize: getSize }
    : { itemSize: itemHeight };

  return (
    <div className={className}>
      <ListComponent
        ref={listRef}
        height={height}
        width={width}
        itemCount={items.length}
        itemData={itemData}
        overscanCount={overscanCount}
        {...listProps}
      >
        {StockListItem}
      </ListComponent>
    </div>
  );
});

VirtualList.displayName = 'VirtualList';

VirtualList.propTypes = {
  items: PropTypes.array.isRequired,
  itemHeight: PropTypes.number,
  height: PropTypes.number,
  width: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  renderItem: PropTypes.func.isRequired,
  onItemClick: PropTypes.func,
  className: PropTypes.string,
  overscanCount: PropTypes.number,
  variableSize: PropTypes.bool,
  getItemSize: PropTypes.func,
  emptyMessage: PropTypes.string,
  loadingMessage: PropTypes.string,
  isLoading: PropTypes.bool,
};

/**
 * 股票卡片渲染函數
 */
export const StockCardRenderer = ({ item, index }) => {
  const priceChange = item.changePercent || item.change_percent || 0;
  const isPositive = priceChange > 0;

  return (
    <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-700">
      <div className="flex-1">
        <div className="flex items-center space-x-2">
          <span className="font-medium text-gray-900 dark:text-white">
            {item.stock_id || item.id}
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {item.name}
          </span>
        </div>
        <div className="text-xs text-gray-400 mt-1">
          {item.industry || item.sector || ''}
        </div>
      </div>
      <div className="text-right">
        <div className="font-mono font-medium text-gray-900 dark:text-white">
          {item.price?.toFixed(2) || item.close?.toFixed(2) || '-'}
        </div>
        <div className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
          {isPositive ? '+' : ''}{priceChange.toFixed(2)}%
        </div>
      </div>
    </div>
  );
};

StockCardRenderer.propTypes = {
  item: PropTypes.object.isRequired,
  index: PropTypes.number.isRequired,
};

/**
 * 推薦股票卡片渲染函數
 */
export const RecommendationCardRenderer = ({ item, index }) => {
  const score = item.score || item.ai_score || 0;
  const signal = item.signal || 'hold';

  const signalColors = {
    buy: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    sell: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    hold: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  };

  return (
    <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-700">
      <div className="flex items-center space-x-3">
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm"
          style={{
            backgroundColor: score >= 80 ? '#10B981' : score >= 60 ? '#F59E0B' : '#EF4444',
          }}
        >
          {score}
        </div>
        <div>
          <div className="font-medium text-gray-900 dark:text-white">
            {item.stock_id || item.id} - {item.name}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {item.reason || item.summary || ''}
          </div>
        </div>
      </div>
      <div>
        <span className={`px-2 py-1 rounded text-xs font-medium ${signalColors[signal]}`}>
          {signal === 'buy' ? '買入' : signal === 'sell' ? '賣出' : '觀望'}
        </span>
      </div>
    </div>
  );
};

RecommendationCardRenderer.propTypes = {
  item: PropTypes.object.isRequired,
  index: PropTypes.number.isRequired,
};

export default VirtualList;
