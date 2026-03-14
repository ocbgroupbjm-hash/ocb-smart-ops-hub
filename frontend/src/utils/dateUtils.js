/**
 * OCB TITAN ERP - Date Utilities
 * Centralized date handling for consistent formatting across all modules
 * 
 * RULES:
 * 1. Backend sends ISO date (YYYY-MM-DD or ISO 8601)
 * 2. Frontend normalizes timezone to tenant/user locale
 * 3. Display format: DD MMM YYYY for Indonesia
 * 4. Input format: YYYY-MM-DD (HTML date input standard)
 * 5. NULL/Invalid date = fallback safe, never placeholder palsu
 */

/**
 * Get today's date in YYYY-MM-DD format (for input fields)
 */
export const getTodayISO = () => {
  return new Date().toISOString().split('T')[0];
};

/**
 * Get start of current month in YYYY-MM-DD format
 */
export const getMonthStartISO = () => {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
};

/**
 * Get end of current month in YYYY-MM-DD format
 */
export const getMonthEndISO = () => {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];
};

/**
 * Parse any date format to Date object
 * Handles: ISO string, Date object, timestamp, various string formats
 * @param {any} dateInput - Date in any format
 * @returns {Date|null} - Parsed Date object or null if invalid
 */
export const parseDate = (dateInput) => {
  if (!dateInput) return null;
  
  // Already a Date object
  if (dateInput instanceof Date) {
    return isNaN(dateInput.getTime()) ? null : dateInput;
  }
  
  // Timestamp (number)
  if (typeof dateInput === 'number') {
    const d = new Date(dateInput);
    return isNaN(d.getTime()) ? null : d;
  }
  
  // String formats
  if (typeof dateInput === 'string') {
    // Handle ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss)
    const isoDate = new Date(dateInput);
    if (!isNaN(isoDate.getTime())) {
      return isoDate;
    }
    
    // Handle DD/MM/YYYY format
    const ddmmyyyy = dateInput.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (ddmmyyyy) {
      const [, dd, mm, yyyy] = ddmmyyyy;
      const d = new Date(parseInt(yyyy), parseInt(mm) - 1, parseInt(dd));
      return isNaN(d.getTime()) ? null : d;
    }
    
    // Handle DD-MM-YYYY format
    const ddmmyyyyDash = dateInput.match(/^(\d{2})-(\d{2})-(\d{4})$/);
    if (ddmmyyyyDash) {
      const [, dd, mm, yyyy] = ddmmyyyyDash;
      const d = new Date(parseInt(yyyy), parseInt(mm) - 1, parseInt(dd));
      return isNaN(d.getTime()) ? null : d;
    }
  }
  
  return null;
};

/**
 * Format date for display (Indonesia locale)
 * @param {any} dateInput - Date in any format
 * @param {string} fallback - Fallback text if date is invalid (default: '-')
 * @returns {string} - Formatted date string
 */
export const formatDateDisplay = (dateInput, fallback = '-') => {
  const date = parseDate(dateInput);
  if (!date) return fallback;
  
  return date.toLocaleDateString('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
};

/**
 * Format date for display (full format with time)
 * @param {any} dateInput - Date in any format
 * @param {string} fallback - Fallback text if date is invalid
 * @returns {string} - Formatted date time string
 */
export const formatDateTimeDisplay = (dateInput, fallback = '-') => {
  const date = parseDate(dateInput);
  if (!date) return fallback;
  
  return date.toLocaleDateString('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * Format date for HTML input field (YYYY-MM-DD)
 * @param {any} dateInput - Date in any format
 * @returns {string} - Date in YYYY-MM-DD format or empty string
 */
export const formatDateInput = (dateInput) => {
  const date = parseDate(dateInput);
  if (!date) return '';
  
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  
  return `${year}-${month}-${day}`;
};

/**
 * Format date for API request (ISO format)
 * @param {any} dateInput - Date in any format
 * @returns {string|null} - ISO date string or null
 */
export const formatDateAPI = (dateInput) => {
  const date = parseDate(dateInput);
  if (!date) return null;
  
  return date.toISOString();
};

/**
 * Format date for table display (compact)
 * @param {any} dateInput - Date in any format
 * @param {string} fallback - Fallback text
 * @returns {string} - Compact formatted date
 */
export const formatDateCompact = (dateInput, fallback = '-') => {
  const date = parseDate(dateInput);
  if (!date) return fallback;
  
  return date.toLocaleDateString('id-ID', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
};

/**
 * PRIORITAS 3: Format date as DD/MM/YYYY (ERP Standard)
 * Standar format tanggal untuk semua modul ERP
 * @param {any} dateInput - Date in any format
 * @param {string} fallback - Fallback text (default: '-')
 * @returns {string} - Date in DD/MM/YYYY format
 */
export const formatDateDDMMYYYY = (dateInput, fallback = '-') => {
  const date = parseDate(dateInput);
  if (!date) return fallback;
  
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  
  return `${day}/${month}/${year}`;
};

/**
 * PRIORITAS 3: Format datetime as DD/MM/YYYY HH:mm (ERP Standard)
 * @param {any} dateInput - Date in any format
 * @param {string} fallback - Fallback text
 * @returns {string} - DateTime in DD/MM/YYYY HH:mm format
 */
export const formatDateTimeDDMMYYYY = (dateInput, fallback = '-') => {
  const date = parseDate(dateInput);
  if (!date) return fallback;
  
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  
  return `${day}/${month}/${year} ${hours}:${minutes}`;
};

/**
 * Format date for aging calculations (days ago/from now)
 * @param {any} dateInput - Date in any format
 * @returns {number} - Days difference (positive = past, negative = future)
 */
export const getDaysFromToday = (dateInput) => {
  const date = parseDate(dateInput);
  if (!date) return 0;
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  date.setHours(0, 0, 0, 0);
  
  const diffTime = today.getTime() - date.getTime();
  return Math.floor(diffTime / (1000 * 60 * 60 * 24));
};

/**
 * Check if date is overdue (past due date)
 * @param {any} dateInput - Due date
 * @returns {boolean} - True if overdue
 */
export const isOverdue = (dateInput) => {
  return getDaysFromToday(dateInput) > 0;
};

/**
 * Get date range for filter presets
 * @param {string} preset - 'today', 'week', 'month', 'quarter', 'year'
 * @returns {{from: string, to: string}} - Date range in YYYY-MM-DD format
 */
export const getDateRangePreset = (preset) => {
  const now = new Date();
  const today = getTodayISO();
  
  switch (preset) {
    case 'today':
      return { from: today, to: today };
    
    case 'week': {
      const start = new Date(now);
      start.setDate(now.getDate() - 7);
      return { from: formatDateInput(start), to: today };
    }
    
    case 'month':
      return { from: getMonthStartISO(), to: today };
    
    case 'quarter': {
      const quarterStart = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1);
      return { from: formatDateInput(quarterStart), to: today };
    }
    
    case 'year': {
      const yearStart = new Date(now.getFullYear(), 0, 1);
      return { from: formatDateInput(yearStart), to: today };
    }
    
    default:
      return { from: '', to: '' };
  }
};

/**
 * Validate date range (from <= to)
 * @param {any} fromDate - Start date
 * @param {any} toDate - End date
 * @returns {boolean} - True if valid range
 */
export const isValidDateRange = (fromDate, toDate) => {
  const from = parseDate(fromDate);
  const to = parseDate(toDate);
  
  if (!from || !to) return true; // Allow partial ranges
  return from <= to;
};

/**
 * Initialize filter dates with defaults (current month)
 * @returns {{dateFrom: string, dateTo: string}}
 */
export const getDefaultFilterDates = () => {
  return {
    dateFrom: getMonthStartISO(),
    dateTo: getTodayISO()
  };
};

/**
 * Initialize single date with today as default
 * @returns {string} - Today's date in YYYY-MM-DD format
 */
export const getDefaultDate = () => {
  return getTodayISO();
};

export default {
  getTodayISO,
  getMonthStartISO,
  getMonthEndISO,
  parseDate,
  formatDateDisplay,
  formatDateTimeDisplay,
  formatDateInput,
  formatDateAPI,
  formatDateCompact,
  formatDateDDMMYYYY,       // PRIORITAS 3: DD/MM/YYYY format
  formatDateTimeDDMMYYYY,   // PRIORITAS 3: DD/MM/YYYY HH:mm format
  getDaysFromToday,
  isOverdue,
  getDateRangePreset,
  isValidDateRange,
  getDefaultFilterDates,
  getDefaultDate
};
