/**
 * StockBuddy 日期工具函數
 * V10.35.4 - 統一日期格式處理
 *
 * 標準格式規範:
 * - 存儲/API: YYYY-MM-DD (2026-01-12)
 * - 顯示/UI: YYYY/MM/DD (2026/01/12)
 * - 簡短顯示: M/D (1/12)
 */

/**
 * 將各種日期格式標準化為 YYYY-MM-DD
 * @param {string|Date} dateInput - 輸入日期
 * @returns {string} - 標準化日期 YYYY-MM-DD
 */
export function normalizeDate(dateInput) {
  if (!dateInput) return '';

  // 如果是 Date 對象
  if (dateInput instanceof Date) {
    return formatDateISO(dateInput);
  }

  const dateStr = String(dateInput).trim();

  // 如果已經是 YYYY-MM-DD 格式
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    return dateStr;
  }

  // YYYY/MM/DD 格式
  if (/^\d{4}\/\d{2}\/\d{2}$/.test(dateStr)) {
    return dateStr.replace(/\//g, '-');
  }

  // YYYYMMDD 格式
  if (/^\d{8}$/.test(dateStr)) {
    return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
  }

  // YYYY.MM.DD 格式
  if (/^\d{4}\.\d{2}\.\d{2}$/.test(dateStr)) {
    return dateStr.replace(/\./g, '-');
  }

  // M/D 或 MM/DD 格式 (當年)
  if (/^\d{1,2}\/\d{1,2}$/.test(dateStr)) {
    const [month, day] = dateStr.split('/');
    const year = new Date().getFullYear();
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
  }

  // 嘗試用 Date 解析
  try {
    const date = new Date(dateStr);
    if (!isNaN(date.getTime())) {
      return formatDateISO(date);
    }
  } catch (e) {
    // 忽略解析錯誤
  }

  return dateStr;
}

/**
 * 格式化為 ISO 日期 (YYYY-MM-DD)
 * @param {Date} date - Date 對象
 * @returns {string}
 */
export function formatDateISO(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * 格式化為顯示用日期 (YYYY/MM/DD)
 * @param {string|Date} dateInput - 輸入日期
 * @returns {string}
 */
export function formatDateDisplay(dateInput) {
  const normalized = normalizeDate(dateInput);
  if (!normalized) return '';
  return normalized.replace(/-/g, '/');
}

/**
 * 格式化為簡短日期 (M/D)
 * @param {string|Date} dateInput - 輸入日期
 * @returns {string}
 */
export function formatDateShort(dateInput) {
  const normalized = normalizeDate(dateInput);
  if (!normalized) return '';

  const [year, month, day] = normalized.split('-');
  return `${parseInt(month)}/${parseInt(day)}`;
}

/**
 * 格式化為中文日期標籤
 * @param {string} dateKey - YYYY-MM-DD 格式的日期
 * @returns {string}
 */
export function formatDateLabel(dateKey) {
  const today = new Date();
  const todayKey = formatDateISO(today);

  if (dateKey === todayKey) {
    return `${dateKey} (今天)`;
  }

  const date = new Date(dateKey);
  if (isNaN(date.getTime())) {
    return dateKey;
  }

  const diffDays = Math.floor((today - date) / (1000 * 60 * 60 * 24));
  const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
  const weekday = weekdays[date.getDay()];

  if (diffDays === 1) return `${dateKey} (昨天)`;
  if (diffDays > 1 && diffDays < 7) return `${dateKey} (${diffDays}天前)`;
  return `${dateKey} (週${weekday})`;
}

/**
 * 獲取今天的 ISO 日期
 * @returns {string} - YYYY-MM-DD
 */
export function getTodayISO() {
  return formatDateISO(new Date());
}

/**
 * 獲取今天的顯示日期
 * @returns {string} - YYYY/MM/DD
 */
export function getTodayDisplay() {
  return formatDateDisplay(new Date());
}

/**
 * 獲取今天的簡短日期
 * @returns {string} - M/D
 */
export function getTodayShort() {
  return formatDateShort(new Date());
}

/**
 * 比較兩個日期是否為同一天
 * @param {string|Date} date1
 * @param {string|Date} date2
 * @returns {boolean}
 */
export function isSameDay(date1, date2) {
  return normalizeDate(date1) === normalizeDate(date2);
}

/**
 * 檢查日期是否為今天
 * @param {string|Date} dateInput
 * @returns {boolean}
 */
export function isToday(dateInput) {
  return normalizeDate(dateInput) === getTodayISO();
}

/**
 * 格式化時間 (HH:MM:SS)
 * @param {Date} date
 * @returns {string}
 */
export function formatTime(date) {
  if (!date || !(date instanceof Date)) return '--:--:--';
  return date.toLocaleTimeString('zh-TW', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * 格式化日期時間 (YYYY/MM/DD HH:MM)
 * @param {string|Date} dateInput
 * @returns {string}
 */
export function formatDateTime(dateInput) {
  if (!dateInput) return '';

  const date = dateInput instanceof Date ? dateInput : new Date(dateInput);
  if (isNaN(date.getTime())) return String(dateInput);

  return date.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default {
  normalizeDate,
  formatDateISO,
  formatDateDisplay,
  formatDateShort,
  formatDateLabel,
  getTodayISO,
  getTodayDisplay,
  getTodayShort,
  isSameDay,
  isToday,
  formatTime,
  formatDateTime,
};
