import * as React from "react"
import { Check, ChevronsUpDown, Search, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

/**
 * SearchableSelect - Reusable searchable dropdown component
 * 
 * Props:
 * - options: Array of {value, label, sublabel?} objects
 * - value: Currently selected value
 * - onValueChange: Callback when value changes
 * - placeholder: Placeholder text
 * - searchPlaceholder: Search input placeholder
 * - emptyText: Text when no results found
 * - disabled: Disable the component
 * - className: Additional CSS classes
 * - allowClear: Show clear button when value selected
 */
export function SearchableSelect({
  options = [],
  value,
  onValueChange,
  placeholder = "Pilih...",
  searchPlaceholder = "Cari...",
  emptyText = "Tidak ditemukan",
  disabled = false,
  className,
  allowClear = true,
  triggerClassName,
  "data-testid": testId,
}) {
  const [open, setOpen] = React.useState(false)
  const [searchQuery, setSearchQuery] = React.useState("")

  const selectedOption = options.find((opt) => opt.value === value)

  const filteredOptions = React.useMemo(() => {
    if (!searchQuery) return options
    const query = searchQuery.toLowerCase()
    return options.filter(
      (opt) =>
        opt.label?.toLowerCase().includes(query) ||
        opt.sublabel?.toLowerCase().includes(query) ||
        opt.value?.toLowerCase().includes(query)
    )
  }, [options, searchQuery])

  const handleSelect = (selectedValue) => {
    onValueChange(selectedValue === value ? "" : selectedValue)
    setOpen(false)
    setSearchQuery("")
  }

  const handleClear = (e) => {
    e.stopPropagation()
    onValueChange("")
    setSearchQuery("")
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
            "w-full justify-between",
            triggerClassName || "bg-red-950/30 border-red-900/30 text-amber-100 hover:bg-red-900/40 hover:text-amber-100",
            !value && "text-gray-400",
            className
          )}
        >
          <span className="truncate">
            {selectedOption ? selectedOption.label : placeholder}
          </span>
          <div className="flex items-center gap-1 ml-2 shrink-0">
            {allowClear && value && (
              <X
                className="h-4 w-4 opacity-50 hover:opacity-100"
                onClick={handleClear}
              />
            )}
            <ChevronsUpDown className="h-4 w-4 opacity-50" />
          </div>
        </Button>
      </PopoverTrigger>
      <PopoverContent className={cn("w-[--radix-popover-trigger-width] p-0", triggerClassName?.includes("bg-gray") ? "bg-gray-800 border-gray-700" : "bg-red-950 border-red-900/50")} align="start">
        <Command className="bg-transparent">
          <div className={cn("flex items-center border-b px-3", triggerClassName?.includes("bg-gray") ? "border-gray-700" : "border-red-900/30")}>
            <Search className={cn("mr-2 h-4 w-4 shrink-0", triggerClassName?.includes("bg-gray") ? "text-gray-400" : "text-amber-100/50")} />
            <input
              placeholder={searchPlaceholder}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={cn("flex h-10 w-full bg-transparent py-3 text-sm outline-none", triggerClassName?.includes("bg-gray") ? "text-white placeholder:text-gray-500" : "text-amber-100 placeholder:text-amber-100/50")}
            />
          </div>
          <CommandList className="max-h-[200px]">
            {filteredOptions.length === 0 ? (
              <div className={cn("py-6 text-center text-sm", triggerClassName?.includes("bg-gray") ? "text-gray-400" : "text-amber-100/50")}>
                {emptyText}
              </div>
            ) : (
              <CommandGroup>
                {filteredOptions.map((option) => (
                  <div
                    key={option.value}
                    onClick={() => handleSelect(option.value)}
                    className={cn(
                      "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none",
                      triggerClassName?.includes("bg-gray") 
                        ? "text-white hover:bg-gray-700" 
                        : "text-amber-100 hover:bg-red-900/50",
                      value === option.value && (triggerClassName?.includes("bg-gray") ? "bg-gray-700" : "bg-red-900/30")
                    )}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        value === option.value ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <div className="flex flex-col">
                      <span>{option.label}</span>
                      {option.sublabel && (
                        <span className={cn("text-xs", triggerClassName?.includes("bg-gray") ? "text-gray-400" : "text-amber-100/50")}>
                          {option.sublabel}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}

/**
 * SearchableMultiSelect - Reusable multi-select searchable dropdown
 */
export function SearchableMultiSelect({
  options = [],
  value = [],
  onValueChange,
  placeholder = "Pilih...",
  searchPlaceholder = "Cari...",
  emptyText = "Tidak ditemukan",
  disabled = false,
  className,
  maxDisplay = 2,
  "data-testid": testId,
}) {
  const [open, setOpen] = React.useState(false)
  const [searchQuery, setSearchQuery] = React.useState("")

  const selectedOptions = options.filter((opt) => value.includes(opt.value))

  const filteredOptions = React.useMemo(() => {
    if (!searchQuery) return options
    const query = searchQuery.toLowerCase()
    return options.filter(
      (opt) =>
        opt.label?.toLowerCase().includes(query) ||
        opt.value?.toLowerCase().includes(query)
    )
  }, [options, searchQuery])

  const handleSelect = (selectedValue) => {
    const newValue = value.includes(selectedValue)
      ? value.filter((v) => v !== selectedValue)
      : [...value, selectedValue]
    onValueChange(newValue)
  }

  const displayText = () => {
    if (selectedOptions.length === 0) return placeholder
    if (selectedOptions.length <= maxDisplay) {
      return selectedOptions.map((o) => o.label).join(", ")
    }
    return `${selectedOptions.length} dipilih`
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
            "w-full justify-between bg-red-950/30 border-red-900/30 text-amber-100 hover:bg-red-900/40",
            !value.length && "text-amber-100/50",
            className
          )}
        >
          <span className="truncate">{displayText()}</span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[--radix-popover-trigger-width] p-0 bg-red-950 border-red-900/50" align="start">
        <Command className="bg-transparent">
          <div className="flex items-center border-b border-red-900/30 px-3">
            <Search className="mr-2 h-4 w-4 shrink-0 text-amber-100/50" />
            <input
              placeholder={searchPlaceholder}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex h-10 w-full bg-transparent py-3 text-sm text-amber-100 outline-none placeholder:text-amber-100/50"
            />
          </div>
          <CommandList className="max-h-[200px]">
            {filteredOptions.length === 0 ? (
              <div className="py-6 text-center text-sm text-amber-100/50">
                {emptyText}
              </div>
            ) : (
              <CommandGroup>
                {filteredOptions.map((option) => (
                  <div
                    key={option.value}
                    onClick={() => handleSelect(option.value)}
                    className={cn(
                      "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none text-amber-100 hover:bg-red-900/50",
                      value.includes(option.value) && "bg-red-900/30"
                    )}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        value.includes(option.value) ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <span>{option.label}</span>
                  </div>
                ))}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}

export default SearchableSelect
