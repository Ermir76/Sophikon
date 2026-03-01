import { useState } from "react";
import { Check, Ban } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/shared/ui/popover";

const COLOR_PRESETS = [
  { label: "Teal", value: "oklch(0.72 0.14 182)" },
  { label: "Blue", value: "oklch(0.65 0.20 240)" },
  { label: "Purple", value: "oklch(0.65 0.20 295)" },
  { label: "Green", value: "oklch(0.72 0.22 155)" },
  { label: "Pink", value: "oklch(0.70 0.18 340)" },
  { label: "Amber", value: "oklch(0.78 0.16 75)" },
  { label: "Orange", value: "oklch(0.72 0.18 30)" },
  { label: "Cyan", value: "oklch(0.75 0.14 195)" },
  { label: "Red", value: "oklch(0.65 0.22 25)" },
  { label: "Indigo", value: "oklch(0.58 0.18 262)" },
] as const;

interface ColorPickerProps {
  value: string | null | undefined;
  onChange: (value: string | null) => void;
}

export function ColorPicker({ value, onChange }: ColorPickerProps) {
  const [open, setOpen] = useState(false);

  const handleSelect = (color: string | null) => {
    onChange(color);
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="size-7 rounded-md border border-border flex items-center justify-center hover:border-ring transition-colors"
          style={value ? { backgroundColor: value } : undefined}
          title={value ?? "No color"}
        >
          {!value && <Ban className="size-3.5 text-muted-foreground" />}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-3" align="start">
        <div className="grid grid-cols-5 gap-2">
          {/* None option */}
          <button
            type="button"
            className="size-7 rounded-full border-2 border-dashed border-muted-foreground/40 flex items-center justify-center hover:border-foreground transition-colors"
            onClick={() => handleSelect(null)}
            title="None"
          >
            {!value && <Check className="size-3.5 text-foreground" />}
          </button>

          {COLOR_PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              className="size-7 rounded-full flex items-center justify-center hover:ring-2 hover:ring-ring hover:ring-offset-1 transition-all"
              style={{ backgroundColor: preset.value }}
              onClick={() => handleSelect(preset.value)}
              title={preset.label}
            >
              {value === preset.value && <Check className="size-3.5 text-white" />}
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}
