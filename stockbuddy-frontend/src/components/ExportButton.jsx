/**
 * 匯出按鈕組件 V10.27
 * V10.15: 支援 CSV 和 Excel 匯出
 * V10.27: 增加 PDF、JSON 匯出，本地資料匯出
 */

import React, { useState } from 'react';
import { API_BASE } from '../config';

// 匯出格式設定
const EXPORT_FORMATS = [
  {
    id: 'csv',
    label: 'CSV 格式',
    icon: '📄',
    desc: '適合 Excel / Google 試算表',
    ext: 'csv',
  },
  {
    id: 'excel',
    label: 'Excel 格式',
    icon: '📊',
    desc: '含格式與樣式 (.xlsx)',
    ext: 'xlsx',
  },
  {
    id: 'pdf',
    label: 'PDF 報告',
    icon: '📑',
    desc: '專業分析報告格式',
    ext: 'pdf',
    local: true,
  },
  {
    id: 'json',
    label: 'JSON 備份',
    icon: '💾',
    desc: '完整資料備份格式',
    ext: 'json',
    local: true,
  },
];

const ExportButton = ({
  type = 'recommendations',
  label = '匯出',
  data = null,
  compact = false,
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  // 產生 PDF 內容 (HTML 轉 PDF)
  const generatePDFContent = (exportData, exportType) => {
    const date = new Date().toLocaleDateString('zh-TW');
    const time = new Date().toLocaleTimeString('zh-TW');

    let title = '股票分析報告';
    let tableHeaders = '';
    let tableRows = '';

    if (exportType === 'recommendations' && Array.isArray(exportData)) {
      title = 'AI 精選股票報告';
      tableHeaders = '<th>代碼</th><th>名稱</th><th>收盤價</th><th>漲跌%</th><th>評分</th><th>信號</th>';
      tableRows = exportData
        .map(
          (s) => `
          <tr>
            <td>${s.stock_id || ''}</td>
            <td>${s.name || ''}</td>
            <td>${s.price?.toFixed(2) || '-'}</td>
            <td class="${(s.change_percent || 0) >= 0 ? 'positive' : 'negative'}">${((s.change_percent || 0) * 100).toFixed(2)}%</td>
            <td>${s.confidence || s.score || '-'}</td>
            <td>${s.signal || '-'}</td>
          </tr>
        `
        )
        .join('');
    } else if (exportType === 'portfolio' && Array.isArray(exportData)) {
      title = '投資組合報告';
      tableHeaders = '<th>代碼</th><th>名稱</th><th>買入價</th><th>現價</th><th>損益%</th>';
      tableRows = exportData
        .map(
          (s) => `
          <tr>
            <td>${s.stock_id || ''}</td>
            <td>${s.name || ''}</td>
            <td>${s.added_price?.toFixed(2) || '-'}</td>
            <td>${s.current_price?.toFixed(2) || '-'}</td>
            <td class="${(s.profit_percent || 0) >= 0 ? 'positive' : 'negative'}">${(s.profit_percent || 0).toFixed(2)}%</td>
          </tr>
        `
        )
        .join('');
    }

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>${title}</title>
        <style>
          body { font-family: 'Microsoft JhengHei', sans-serif; padding: 40px; }
          h1 { color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }
          .meta { color: #64748b; margin-bottom: 20px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th { background: #1e293b; color: white; padding: 12px; text-align: left; }
          td { padding: 10px; border-bottom: 1px solid #e2e8f0; }
          tr:nth-child(even) { background: #f8fafc; }
          .positive { color: #10b981; }
          .negative { color: #ef4444; }
          .footer { margin-top: 30px; color: #94a3b8; font-size: 12px; text-align: center; }
        </style>
      </head>
      <body>
        <h1>${title}</h1>
        <div class="meta">產出日期：${date} ${time} | StockBuddy 股票分析系統</div>
        <table>
          <thead><tr>${tableHeaders}</tr></thead>
          <tbody>${tableRows}</tbody>
        </table>
        <div class="footer">本報告由 StockBuddy V10.27 自動產出，僅供參考，不構成投資建議。</div>
      </body>
      </html>
    `;
  };

  // 本地匯出 PDF
  const exportLocalPDF = (exportData, exportType) => {
    const htmlContent = generatePDFContent(exportData, exportType);
    const printWindow = window.open('', '_blank');
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.print();
    };
  };

  // 本地匯出 JSON
  const exportLocalJSON = (exportData, exportType) => {
    const jsonContent = JSON.stringify(
      {
        exportType,
        exportDate: new Date().toISOString(),
        version: 'V10.27',
        data: exportData,
      },
      null,
      2
    );

    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `stockbuddy_${exportType}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  // 本地匯出 CSV
  const exportLocalCSV = (exportData, exportType) => {
    if (!Array.isArray(exportData) || exportData.length === 0) {
      alert('沒有資料可匯出');
      return;
    }

    // 建立 CSV 內容
    const headers = Object.keys(exportData[0]);
    const csvRows = [
      headers.join(','),
      ...exportData.map((row) =>
        headers.map((header) => {
          const val = row[header];
          // 處理包含逗號或引號的值
          if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
            return `"${val.replace(/"/g, '""')}"`;
          }
          return val ?? '';
        }).join(',')
      ),
    ];

    const csvContent = '\uFEFF' + csvRows.join('\n'); // BOM for UTF-8
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `stockbuddy_${exportType}_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const handleExport = async (format) => {
    setIsExporting(true);
    setShowMenu(false);

    try {
      const formatConfig = EXPORT_FORMATS.find((f) => f.id === format);

      // 如果有提供本地資料且是本地匯出格式
      if (data && formatConfig?.local) {
        if (format === 'pdf') {
          exportLocalPDF(data, type);
        } else if (format === 'json') {
          exportLocalJSON(data, type);
        }
        return;
      }

      // 如果有本地資料且是 CSV
      if (data && format === 'csv') {
        exportLocalCSV(data, type);
        return;
      }

      // 否則呼叫 API
      let endpoint = '';
      let filename = '';

      switch (type) {
        case 'recommendations':
          endpoint = `/api/stocks/export/recommendations/${format}`;
          filename = `stockbuddy_recommendations.${formatConfig?.ext || format}`;
          break;
        case 'portfolio':
          endpoint = `/api/stocks/export/portfolio/${format}`;
          filename = `stockbuddy_portfolio.${formatConfig?.ext || format}`;
          break;
        default:
          endpoint = `/api/stocks/export/recommendations/${format}`;
          filename = `export.${formatConfig?.ext || format}`;
      }

      const response = await fetch(`${API_BASE}${endpoint}`);

      if (!response.ok) {
        throw new Error('匯出失敗');
      }

      // 取得檔案名稱（從 header 或使用預設）
      const contentDisposition = response.headers.get('Content-Disposition');
      if (contentDisposition) {
        const match = contentDisposition.match(/filename=(.+)/);
        if (match) {
          filename = match[1];
        }
      }

      // 下載檔案
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('匯出錯誤:', err);
      alert('匯出失敗，請稍後再試');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        disabled={isExporting}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
          isExporting
            ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
            : 'bg-emerald-600 hover:bg-emerald-500 text-white'
        }`}
      >
        {isExporting ? (
          <>
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            匯出中...
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {label}
          </>
        )}
      </button>

      {/* 下拉選單 */}
      {showMenu && (
        <div className="absolute top-full mt-2 right-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 overflow-hidden min-w-[200px]">
          {EXPORT_FORMATS.map((format, index) => (
            <button
              key={format.id}
              onClick={() => handleExport(format.id)}
              className={`flex items-center gap-3 w-full px-4 py-3 text-left text-white hover:bg-slate-700 transition-colors ${
                index > 0 ? 'border-t border-slate-700' : ''
              }`}
            >
              <span className="text-lg">{format.icon}</span>
              <div>
                <div className="font-medium">{format.label}</div>
                <div className="text-xs text-slate-400">{format.desc}</div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* 點擊外部關閉選單 */}
      {showMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowMenu(false)}
        />
      )}
    </div>
  );
};

export default ExportButton;
