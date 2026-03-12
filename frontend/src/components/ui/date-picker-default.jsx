import * as React from "react"
import { format } from "date-fns"
import { id } from "date-fns/locale"
import { Calendar as CalendarIcon, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

/**
 * DatePickerWithDefault - Date picker with today as default
 * 
 * Props:
 * - value: Selected date (Date object or ISO string)
 * - onValueChange: Callback when date changes
 * - placeholder: Placeholder text
 * - defaultToday: Whether to default to today (default: true)
 * - disabled: Disable the component
 * - className: Additional CSS classes
 * - allowClear: Show clear button
 * - minDate: Minimum selectable date
 * - maxDate: Maximum selectable date
 * - dateFormat: Display format (default: "dd MMM yyyy")
 */
export function DatePickerWithDefault({
  value,
  onValueChange,
  placeholder = "Pilih tanggal",
  defaultToday = true,
  disabled = false,
  className,
  allowClear = true,
  minDate,
  maxDate,
  dateFormat = "dd MMM yyyy",
  "data-testid": testId,
}) {
  const [open, setOpen] = React.useState(false)

  // Initialize with today if defaultToday is true and no value
  React.useEffect(() => {
    if (defaultToday && !value) {
      onValueChange(new Date())
    }
  }, []) // Only run once on mount

  const dateValue = React.useMemo(() => {
    if (!value) return undefined
    if (value instanceof Date) return value
    return new Date(value)
  }, [value])

  const handleSelect = (date) => {
    onValueChange(date)
    setOpen(false)
  }

  const handleClear = (e) => {
    e.stopPropagation()
    onValueChange(null)
  }

  const disabledDays = React.useMemo(() => {
    const disabled = []
    if (minDate) disabled.push({ before: new Date(minDate) })
    if (maxDate) disabled.push({ after: new Date(maxDate) })
    return disabled
  }, [minDate, maxDate])

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          disabled={disabled}
          data-testid={testId}
          className={cn(
            "w-full justify-start text-left font-normal bg-red-950/30 border-red-900/30 text-amber-100 hover:bg-red-900/40 hover:text-amber-100",
            !dateValue && "text-amber-100/50",
            className
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          <span className="flex-1">
            {dateValue ? format(dateValue, dateFormat, { locale: id }) : placeholder}
          </span>
          {allowClear && dateValue && (
            <X
              className="ml-2 h-4 w-4 opacity-50 hover:opacity-100"
              onClick={handleClear}
            />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0 bg-red-950 border-red-900/50" align="start">
        <Calendar
          mode="single"
          selected={dateValue}
          onSelect={handleSelect}
          disabled={disabledDays}
          initialFocus
          locale={id}
          className="text-amber-100"
        />
        <div className="border-t border-red-900/30 p-2 flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="flex-1 text-amber-100 hover:bg-red-900/50"
            onClick={() => handleSelect(new Date())}
          >
            Hari Ini
          </Button>
          {allowClear && (
            <Button
              variant="ghost"
              size="sm"
              className="flex-1 text-amber-100/70 hover:bg-red-900/50"
              onClick={(e) => {
                handleClear(e)
                setOpen(false)
              }}
            >
              Hapus
            </Button>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}

/**
 * DateRangePickerWithDefault - Date range picker with today as default
 */
export function DateRangePickerWithDefault({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  startPlaceholder = "Dari tanggal",
  endPlaceholder = "Sampai tanggal",
  defaultToday = true,
  disabled = false,
  className,
  dateFormat = "dd MMM yyyy",
  "data-testid": testId,
}) {
  // Initialize with today if defaultToday
  React.useEffect(() => {
    if (defaultToday) {
      if (!startDate) onStartDateChange(new Date())
      if (!endDate) onEndDateChange(new Date())
    }
  }, [])

  return (
    <div className={cn("flex gap-2 items-center", className)} data-testid={testId}>
      <DatePickerWithDefault
        value={startDate}
        onValueChange={onStartDateChange}
        placeholder={startPlaceholder}
        defaultToday={false}
        disabled={disabled}
        maxDate={endDate}
        dateFormat={dateFormat}
        allowClear={false}
        data-testid={`${testId}-start`}
      />
      <span className="text-amber-100/50">-</span>
      <DatePickerWithDefault
        value={endDate}
        onValueChange={onEndDateChange}
        placeholder={endPlaceholder}
        defaultToday={false}
        disabled={disabled}
        minDate={startDate}
        dateFormat={dateFormat}
        allowClear={false}
        data-testid={`${testId}-end`}
      />
    </div>
  )
}

export default DatePickerWithDefault
