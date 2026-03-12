import * as React from "react"
import { Check, ChevronsUpDown, Search } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

/**
 * SearchableEnumSelect - Searchable dropdown for enum/option fields
 * 
 * Designed for fields like:
 * - Jenis mutasi (stock_in, stock_out, transfer, adjustment)
 * - Status (draft, pending, approved, rejected)
 * - Tipe transaksi (cash, credit, bank_transfer)
 * - Payment method
 * - Urgency level
 * 
 * Props:
 * - options: Array of {value, label, color?, icon?} objects
 * - value: Currently selected value
 * - onValueChange: Callback when value changes
 * - placeholder: Placeholder text
 * - searchPlaceholder: Search input placeholder
 * - emptyText: Text when no results found
 * - disabled: Disable the component
 * - showAllOption: Show "Semua" option at top
 * - allOptionLabel: Label for all option
 */
export function SearchableEnumSelect({
  options = [],
  value,
  onValueChange,
  placeholder = "Pilih...",
  searchPlaceholder = "Ketik untuk filter...",
  emptyText = "Tidak ditemukan",
  disabled = false,
  className,
  showAllOption = false,
  allOptionLabel = "Semua",
  "data-testid": testId,
}) {
  const [open, setOpen] = React.useState(false)
  const [searchQuery, setSearchQuery] = React.useState("")

  const allOptions = React.useMemo(() => {
    if (showAllOption) {
      return [{ value: "", label: allOptionLabel, isAll: true }, ...options]
    }
    return options
  }, [options, showAllOption, allOptionLabel])

  const selectedOption = allOptions.find((opt) => opt.value === value)

  const filteredOptions = React.useMemo(() => {
    if (!searchQuery) return allOptions
    const query = searchQuery.toLowerCase()
    return allOptions.filter(
      (opt) =>
        opt.label?.toLowerCase().includes(query) ||
        opt.value?.toLowerCase().includes(query)
    )
  }, [allOptions, searchQuery])

  const handleSelect = (selectedValue) => {
    onValueChange(selectedValue)
    setOpen(false)
    setSearchQuery("")
  }

  const getColorClass = (color) => {
    const colorMap = {
      green: "bg-green-500/20 text-green-400",
      red: "bg-red-500/20 text-red-400",
      yellow: "bg-yellow-500/20 text-yellow-400",
      blue: "bg-blue-500/20 text-blue-400",
      purple: "bg-purple-500/20 text-purple-400",
      orange: "bg-orange-500/20 text-orange-400",
      gray: "bg-gray-500/20 text-gray-400",
    }
    return colorMap[color] || ""
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          data-testid={testId}
          className={cn(
            "w-full justify-between bg-red-950/30 border-red-900/30 text-amber-100 hover:bg-red-900/40 hover:text-amber-100",
            !value && "text-amber-100/50",
            className
          )}
        >
          <span className="flex items-center gap-2 truncate">
            {selectedOption?.color && (
              <span className={cn("px-1.5 py-0.5 rounded text-xs", getColorClass(selectedOption.color))}>
                {selectedOption.label}
              </span>
            )}
            {!selectedOption?.color && (selectedOption ? selectedOption.label : placeholder)}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[--radix-popover-trigger-width] p-0 bg-red-950 border-red-900/50" align="start">
        <div className="flex items-center border-b border-red-900/30 px-3">
          <Search className="mr-2 h-4 w-4 shrink-0 text-amber-100/50" />
          <input
            placeholder={searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex h-10 w-full bg-transparent py-3 text-sm text-amber-100 outline-none placeholder:text-amber-100/50"
            autoFocus
          />
        </div>
        <div className="max-h-[200px] overflow-y-auto">
          {filteredOptions.length === 0 ? (
            <div className="py-6 text-center text-sm text-amber-100/50">
              {emptyText}
            </div>
          ) : (
            <div className="p-1">
              {filteredOptions.map((option) => (
                <div
                  key={option.value}
                  onClick={() => handleSelect(option.value)}
                  className={cn(
                    "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none text-amber-100 hover:bg-red-900/50",
                    value === option.value && "bg-red-900/30"
                  )}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      value === option.value ? "opacity-100" : "opacity-0"
                    )}
                  />
                  {option.color ? (
                    <span className={cn("px-1.5 py-0.5 rounded text-xs", getColorClass(option.color))}>
                      {option.label}
                    </span>
                  ) : (
                    <span className={option.isAll ? "text-amber-100/70" : ""}>
                      {option.label}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}

// Pre-defined enum options for common use cases
export const STOCK_MOVEMENT_TYPES = [
  { value: "stock_in", label: "Stock In", color: "green" },
  { value: "stock_out", label: "Stock Out", color: "red" },
  { value: "transfer_in", label: "Transfer In", color: "blue" },
  { value: "transfer_out", label: "Transfer Out", color: "purple" },
  { value: "adjustment_in", label: "Adjustment (+)", color: "green" },
  { value: "adjustment_out", label: "Adjustment (-)", color: "red" },
  { value: "purchase_in", label: "Purchase In", color: "green" },
  { value: "sales_out", label: "Sales Out", color: "orange" },
  { value: "return_in", label: "Return In", color: "blue" },
  { value: "return_out", label: "Return Out", color: "purple" },
]

export const STATUS_OPTIONS = [
  { value: "draft", label: "Draft", color: "gray" },
  { value: "pending", label: "Pending", color: "yellow" },
  { value: "reviewed", label: "Reviewed", color: "blue" },
  { value: "approved", label: "Approved", color: "green" },
  { value: "rejected", label: "Rejected", color: "red" },
  { value: "completed", label: "Completed", color: "green" },
  { value: "cancelled", label: "Cancelled", color: "red" },
]

export const URGENCY_OPTIONS = [
  { value: "critical", label: "Critical", color: "red" },
  { value: "high", label: "High", color: "orange" },
  { value: "medium", label: "Medium", color: "yellow" },
  { value: "low", label: "Low", color: "green" },
]

export const PAYMENT_METHOD_OPTIONS = [
  { value: "cash", label: "Tunai (Cash)" },
  { value: "bank_transfer", label: "Transfer Bank" },
  { value: "credit", label: "Kredit" },
  { value: "debit", label: "Debit Card" },
  { value: "qris", label: "QRIS" },
  { value: "e_wallet", label: "E-Wallet" },
]

export const TRANSACTION_TYPE_OPTIONS = [
  { value: "sales", label: "Penjualan" },
  { value: "purchase", label: "Pembelian" },
  { value: "return_sales", label: "Retur Penjualan" },
  { value: "return_purchase", label: "Retur Pembelian" },
  { value: "adjustment", label: "Adjustment" },
  { value: "transfer", label: "Transfer" },
]

export default SearchableEnumSelect
