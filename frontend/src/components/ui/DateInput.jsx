/**
 * OCB TITAN ERP - DateInput Component
 * Standardized date input for all modules
 * 
 * Features:
 * - Consistent styling with ERP theme
 * - Auto-default to today if defaultToday=true
 * - Proper value handling (never shows placeholder for actual dates)
 * - Locale-aware display
 */

import React, { useEffect, useMemo } from 'react';
import { Calendar } from 'lucide-react';
import { formatDateInput, getTodayISO, parseDate } from '../../utils/dateUtils';

/**
 * DateInput - Standard date input component
 * 
 * @param {Object} props
 * @param {string} props.value - Date value (any format)
 * @param {function} props.onChange - Change handler (receives YYYY-MM-DD string)
 * @param {string} props.label - Label text
 * @param {boolean} props.defaultToday - Default to today if no value (default: false)
 * @param {boolean} props.required - Required field indicator
 * @param {boolean} props.disabled - Disabled state
 * @param {string} props.min - Minimum date (YYYY-MM-DD)
 * @param {string} props.max - Maximum date (YYYY-MM-DD)
 * @param {string} props.className - Additional CSS classes
 * @param {string} props.testId - data-testid attribute
 */
export const DateInput = ({
  value,
  onChange,
  label,
  defaultToday = false,
  required = false,
  disabled = false,
  min,
  max,
  className = '',
  testId,
  error,
  ...props
}) => {
  // Normalize value to YYYY-MM-DD format
  const normalizedValue = useMemo(() => {
    const formatted = formatDateInput(value);
    return formatted;
  }, [value]);

  // Set default to today on mount if defaultToday is true and no value
  useEffect(() => {
    if (defaultToday && !value && onChange) {
      onChange(getTodayISO());
    }
  }, []); // Only run once on mount

  const handleChange = (e) => {
    if (onChange) {
      onChange(e.target.value);
    }
  };

  return (
    <div className={`date-input-wrapper ${className}`}>
      {label && (
        <label className="block text-xs text-gray-400 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        <input
          type="date"
          value={normalizedValue}
          onChange={handleChange}
          disabled={disabled}
          min={min}
          max={max}
          data-testid={testId}
          className={`
            w-full px-3 py-1.5 
            bg-[#0a0608] border border-red-900/30 rounded 
            text-sm text-white
            focus:outline-none focus:border-amber-500/50
            disabled:opacity-50 disabled:cursor-not-allowed
            [&::-webkit-calendar-picker-indicator]:filter 
            [&::-webkit-calendar-picker-indicator]:invert
            ${error ? 'border-red-500' : ''}
          `}
          {...props}
        />
      </div>
      {error && (
        <p className="text-xs text-red-500 mt-1">{error}</p>
      )}
    </div>
  );
};

/**
 * DateRangeFilter - Standard date range filter for lists/reports
 * 
 * @param {Object} props
 * @param {string} props.dateFrom - Start date
 * @param {string} props.dateTo - End date
 * @param {function} props.onDateFromChange - Start date change handler
 * @param {function} props.onDateToChange - End date change handler
 * @param {boolean} props.defaultToMonth - Default to current month
 * @param {string} props.className - Additional CSS classes
 */
export const DateRangeFilter = ({
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
  defaultToMonth = true,
  className = '',
  fromLabel = 'Dari Tanggal',
  toLabel = 'Sampai Tanggal',
  testIdPrefix = 'date-filter'
}) => {
  // Set default dates on mount
  useEffect(() => {
    if (defaultToMonth) {
      if (!dateFrom && onDateFromChange) {
        const now = new Date();
        const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
        onDateFromChange(formatDateInput(monthStart));
      }
      if (!dateTo && onDateToChange) {
        onDateToChange(getTodayISO());
      }
    }
  }, []); // Only run once on mount

  return (
    <div className={`flex gap-2 items-end ${className}`}>
      <DateInput
        value={dateFrom}
        onChange={onDateFromChange}
        label={fromLabel}
        max={dateTo}
        testId={`${testIdPrefix}-from`}
      />
      <DateInput
        value={dateTo}
        onChange={onDateToChange}
        label={toLabel}
        min={dateFrom}
        testId={`${testIdPrefix}-to`}
      />
    </div>
  );
};

/**
 * FormDateInput - Date input styled for forms/modals
 */
export const FormDateInput = ({
  value,
  onChange,
  label,
  required = false,
  disabled = false,
  error,
  className = '',
  testId,
  ...props
}) => {
  const normalizedValue = useMemo(() => formatDateInput(value), [value]);

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-300 mb-1.5">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <input
        type="date"
        value={normalizedValue}
        onChange={(e) => onChange && onChange(e.target.value)}
        disabled={disabled}
        data-testid={testId}
        className={`
          w-full px-3 py-2 
          bg-[#0a0608] border border-red-900/30 rounded-lg 
          text-white
          focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/20
          disabled:opacity-50 disabled:cursor-not-allowed
          [&::-webkit-calendar-picker-indicator]:filter 
          [&::-webkit-calendar-picker-indicator]:invert
          ${error ? 'border-red-500' : ''}
        `}
        {...props}
      />
      {error && (
        <p className="text-xs text-red-500 mt-1">{error}</p>
      )}
    </div>
  );
};

export default DateInput;
