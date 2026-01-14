/**
 * K 線圖組件 V10.15
 * 專業互動式蠟燭圖，包含技術指標
 *
 * 功能：
 * - 蠟燭圖（開高低收）
 * - 成交量柱狀圖
 * - MA 移動平均線（5/10/20/60日）
 * - MACD 指標
 * - RSI 指標
 * - 布林通道
 * - 縮放與平移
 */

import React, { useEffect, useRef, useState, useMemo } from 'react';

// K線圖組件
const CandlestickChart = ({
  data,
  stockId,
  stockName,
  width = 800,
  height = 500,
  showVolume = true,
  showMA = true,
  showMACD = false,
  showRSI = false,
  showBollinger = false,
}) => {
  const canvasRef = useRef(null);
  const [hoveredCandle, setHoveredCandle] = useState(null);
  const [viewRange, setViewRange] = useState({ start: 0, end: 60 }); // 顯示範圍

  // 計算技術指標
  const indicators = useMemo(() => {
    if (!data || data.length === 0) return {};

    const closes = data.map(d => d.close);

    // 移動平均線
    const calcMA = (prices, period) => {
      const result = [];
      for (let i = 0; i < prices.length; i++) {
        if (i < period - 1) {
          result.push(null);
        } else {
          const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
          result.push(sum / period);
        }
      }
      return result;
    };

    // RSI 計算
    const calcRSI = (prices, period = 14) => {
      const result = [];
      let gains = 0;
      let losses = 0;

      for (let i = 0; i < prices.length; i++) {
        if (i === 0) {
          result.push(50);
          continue;
        }

        const change = prices[i] - prices[i - 1];

        if (i <= period) {
          if (change > 0) gains += change;
          else losses -= change;

          if (i === period) {
            const avgGain = gains / period;
            const avgLoss = losses / period;
            const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
            result.push(100 - (100 / (1 + rs)));
          } else {
            result.push(null);
          }
        } else {
          const prevGain = change > 0 ? change : 0;
          const prevLoss = change < 0 ? -change : 0;

          gains = (gains * (period - 1) + prevGain) / period;
          losses = (losses * (period - 1) + prevLoss) / period;

          const rs = losses === 0 ? 100 : gains / losses;
          result.push(100 - (100 / (1 + rs)));
        }
      }

      return result;
    };

    // MACD 計算
    const calcMACD = (prices, fast = 12, slow = 26, signal = 9) => {
      const emaFast = [];
      const emaSlow = [];
      const macdLine = [];
      const signalLine = [];
      const histogram = [];

      // EMA 計算
      const calcEMA = (price, prev, period) => {
        const k = 2 / (period + 1);
        return price * k + prev * (1 - k);
      };

      for (let i = 0; i < prices.length; i++) {
        if (i === 0) {
          emaFast.push(prices[i]);
          emaSlow.push(prices[i]);
        } else {
          emaFast.push(calcEMA(prices[i], emaFast[i - 1], fast));
          emaSlow.push(calcEMA(prices[i], emaSlow[i - 1], slow));
        }

        if (i >= slow - 1) {
          const macd = emaFast[i] - emaSlow[i];
          macdLine.push(macd);

          if (macdLine.length === 1) {
            signalLine.push(macd);
          } else {
            signalLine.push(calcEMA(macd, signalLine[signalLine.length - 1], signal));
          }

          histogram.push(macd - signalLine[signalLine.length - 1]);
        } else {
          macdLine.push(null);
          signalLine.push(null);
          histogram.push(null);
        }
      }

      return { macd: macdLine, signal: signalLine, histogram };
    };

    // 布林通道
    const calcBollinger = (prices, period = 20, stdDev = 2) => {
      const upper = [];
      const middle = [];
      const lower = [];

      for (let i = 0; i < prices.length; i++) {
        if (i < period - 1) {
          upper.push(null);
          middle.push(null);
          lower.push(null);
        } else {
          const slice = prices.slice(i - period + 1, i + 1);
          const avg = slice.reduce((a, b) => a + b, 0) / period;
          const variance = slice.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / period;
          const std = Math.sqrt(variance);

          middle.push(avg);
          upper.push(avg + stdDev * std);
          lower.push(avg - stdDev * std);
        }
      }

      return { upper, middle, lower };
    };

    return {
      ma5: calcMA(closes, 5),
      ma10: calcMA(closes, 10),
      ma20: calcMA(closes, 20),
      ma60: calcMA(closes, 60),
      rsi: calcRSI(closes, 14),
      macd: calcMACD(closes),
      bollinger: calcBollinger(closes),
    };
  }, [data]);

  // 繪製圖表
  useEffect(() => {
    if (!data || data.length === 0 || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;

    // 設定畫布大小
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);

    // 清除畫布
    ctx.fillStyle = '#1e293b'; // slate-800
    ctx.fillRect(0, 0, width, height);

    // 計算顯示區域
    const displayData = data.slice(viewRange.start, viewRange.end);
    if (displayData.length === 0) return;

    // 計算價格範圍
    const prices = displayData.flatMap(d => [d.high, d.low]);
    const minPrice = Math.min(...prices) * 0.995;
    const maxPrice = Math.max(...prices) * 1.005;

    // 計算成交量範圍
    const volumes = displayData.map(d => d.volume || 0);
    const maxVolume = Math.max(...volumes);

    // 版面配置
    const padding = { top: 30, right: 60, bottom: 30, left: 10 };
    const chartHeight = showVolume ? height * 0.65 : height * 0.85;
    const volumeHeight = showVolume ? height * 0.2 : 0;

    const chartWidth = width - padding.left - padding.right;
    const candleWidth = chartWidth / displayData.length * 0.7;
    const candleSpacing = chartWidth / displayData.length;

    // 價格座標轉換
    const priceToY = (price) => {
      return padding.top + (maxPrice - price) / (maxPrice - minPrice) * (chartHeight - padding.top);
    };

    // 繪製網格
    ctx.strokeStyle = '#334155'; // slate-700
    ctx.lineWidth = 0.5;

    // 橫向網格線 + 價格標籤
    const priceStep = (maxPrice - minPrice) / 5;
    ctx.fillStyle = '#94a3b8'; // slate-400
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';

    for (let i = 0; i <= 5; i++) {
      const price = minPrice + priceStep * i;
      const y = priceToY(price);

      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      ctx.fillText(price.toFixed(2), width - 5, y + 4);
    }

    // 繪製 K 線
    displayData.forEach((candle, i) => {
      const x = padding.left + i * candleSpacing + candleSpacing / 2;
      const isUp = candle.close >= candle.open;

      // 蠟燭顏色
      const color = isUp ? '#ef4444' : '#22c55e'; // 紅漲綠跌
      ctx.fillStyle = color;
      ctx.strokeStyle = color;

      // 繪製影線
      ctx.beginPath();
      ctx.moveTo(x, priceToY(candle.high));
      ctx.lineTo(x, priceToY(candle.low));
      ctx.lineWidth = 1;
      ctx.stroke();

      // 繪製蠟燭本體
      const openY = priceToY(candle.open);
      const closeY = priceToY(candle.close);
      const bodyHeight = Math.max(Math.abs(closeY - openY), 1);

      ctx.fillRect(
        x - candleWidth / 2,
        Math.min(openY, closeY),
        candleWidth,
        bodyHeight
      );
    });

    // 繪製 MA 移動平均線
    if (showMA && indicators.ma5) {
      const drawMA = (maData, color, lineWidth = 1) => {
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;

        let started = false;
        maData.slice(viewRange.start, viewRange.end).forEach((ma, i) => {
          if (ma === null) return;
          const x = padding.left + i * candleSpacing + candleSpacing / 2;
          const y = priceToY(ma);

          if (!started) {
            ctx.moveTo(x, y);
            started = true;
          } else {
            ctx.lineTo(x, y);
          }
        });

        ctx.stroke();
      };

      drawMA(indicators.ma5, '#f59e0b', 1.5);   // 黃色 MA5
      drawMA(indicators.ma10, '#3b82f6', 1.5);  // 藍色 MA10
      drawMA(indicators.ma20, '#a855f7', 1.5);  // 紫色 MA20
      if (indicators.ma60) {
        drawMA(indicators.ma60, '#ec4899', 1);  // 粉色 MA60
      }
    }

    // 繪製布林通道
    if (showBollinger && indicators.bollinger) {
      const drawBB = (bbData, color) => {
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 5]);

        let started = false;
        bbData.slice(viewRange.start, viewRange.end).forEach((val, i) => {
          if (val === null) return;
          const x = padding.left + i * candleSpacing + candleSpacing / 2;
          const y = priceToY(val);

          if (!started) {
            ctx.moveTo(x, y);
            started = true;
          } else {
            ctx.lineTo(x, y);
          }
        });

        ctx.stroke();
        ctx.setLineDash([]);
      };

      drawBB(indicators.bollinger.upper, '#38bdf8');
      drawBB(indicators.bollinger.lower, '#38bdf8');
    }

    // 繪製成交量
    if (showVolume && maxVolume > 0) {
      const volumeTop = chartHeight + 15;
      const volumeScale = volumeHeight / maxVolume;

      displayData.forEach((candle, i) => {
        const x = padding.left + i * candleSpacing + candleSpacing / 2;
        const isUp = candle.close >= candle.open;
        const barHeight = (candle.volume || 0) * volumeScale;

        ctx.fillStyle = isUp ? 'rgba(239, 68, 68, 0.5)' : 'rgba(34, 197, 94, 0.5)';
        ctx.fillRect(
          x - candleWidth / 2,
          volumeTop + volumeHeight - barHeight,
          candleWidth,
          barHeight
        );
      });

      // 成交量標籤
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(`Vol: ${(maxVolume / 1000).toFixed(0)}K`, width - 5, volumeTop + 12);
    }

    // 繪製 MA 圖例
    if (showMA) {
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'left';

      const legends = [
        { label: 'MA5', color: '#f59e0b' },
        { label: 'MA10', color: '#3b82f6' },
        { label: 'MA20', color: '#a855f7' },
        { label: 'MA60', color: '#ec4899' },
      ];

      legends.forEach((legend, i) => {
        const x = padding.left + i * 60;
        ctx.fillStyle = legend.color;
        ctx.fillRect(x, 8, 15, 3);
        ctx.fillText(legend.label, x + 18, 12);
      });
    }

    // 標題
    ctx.fillStyle = '#f8fafc';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(`${stockName || stockId} K線圖`, width - padding.right, 20);

  }, [data, viewRange, width, height, showVolume, showMA, showBollinger, indicators, stockId, stockName]);

  // 滾輪縮放
  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 5 : -5;

    setViewRange(prev => {
      const newEnd = Math.min(data.length, Math.max(prev.start + 20, prev.end + delta));
      return { ...prev, end: newEnd };
    });
  };

  // 滑鼠移動顯示資訊
  const handleMouseMove = (e) => {
    if (!data || data.length === 0) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;

    const padding = { left: 10, right: 60 };
    const chartWidth = width - padding.left - padding.right;
    const displayData = data.slice(viewRange.start, viewRange.end);
    const candleSpacing = chartWidth / displayData.length;

    const index = Math.floor((x - padding.left) / candleSpacing);

    if (index >= 0 && index < displayData.length) {
      setHoveredCandle(displayData[index]);
    } else {
      setHoveredCandle(null);
    }
  };

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-slate-800 rounded-xl">
        <p className="text-slate-400">無 K 線資料</p>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* 資訊浮動框 */}
      {hoveredCandle && (
        <div className="absolute top-2 left-2 bg-slate-900/90 border border-slate-700 rounded-lg p-3 text-sm z-10">
          <div className="text-slate-400 mb-1">{hoveredCandle.date}</div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            <span className="text-slate-500">開:</span>
            <span className="text-white">{hoveredCandle.open?.toFixed(2)}</span>
            <span className="text-slate-500">高:</span>
            <span className="text-red-400">{hoveredCandle.high?.toFixed(2)}</span>
            <span className="text-slate-500">低:</span>
            <span className="text-emerald-400">{hoveredCandle.low?.toFixed(2)}</span>
            <span className="text-slate-500">收:</span>
            <span className={hoveredCandle.close >= hoveredCandle.open ? 'text-red-400' : 'text-emerald-400'}>
              {hoveredCandle.close?.toFixed(2)}
            </span>
            <span className="text-slate-500">量:</span>
            <span className="text-white">{((hoveredCandle.volume || 0) / 1000).toFixed(0)}K</span>
          </div>
        </div>
      )}

      {/* 圖表 Canvas */}
      <canvas
        ref={canvasRef}
        onWheel={handleWheel}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHoveredCandle(null)}
        className="rounded-xl cursor-crosshair"
      />

      {/* 控制按鈕 */}
      <div className="flex justify-center gap-2 mt-2">
        <button
          onClick={() => setViewRange({ start: 0, end: Math.min(30, data.length) })}
          className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-white rounded"
        >
          1月
        </button>
        <button
          onClick={() => setViewRange({ start: 0, end: Math.min(60, data.length) })}
          className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-white rounded"
        >
          3月
        </button>
        <button
          onClick={() => setViewRange({ start: 0, end: Math.min(120, data.length) })}
          className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-white rounded"
        >
          6月
        </button>
        <button
          onClick={() => setViewRange({ start: 0, end: data.length })}
          className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-white rounded"
        >
          全部
        </button>
      </div>
    </div>
  );
};

export default CandlestickChart;
