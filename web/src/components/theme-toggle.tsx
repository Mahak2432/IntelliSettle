"use client";

import { Check, Monitor, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useLang } from "@/lib/i18n";

const OPTIONS = [
  { value: "light", icon: Sun, en: "Light", hi: "हल्का" },
  { value: "dark", icon: Moon, en: "Dark", hi: "गहरा" },
  { value: "system", icon: Monitor, en: "Same as device", hi: "डिवाइस के अनुसार" },
] as const;

export function ThemeToggle({ english = false }: { english?: boolean }) {
  const { theme, setTheme } = useTheme();
  const { lang } = useLang();
  const l = english ? "en" : lang;
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant="outline"
            size="icon"
            className="size-10 rounded-full bg-surface text-indigo"
            aria-label={l === "hi" ? "थीम बदलें" : "Change theme"}
          />
        }
      >
        {/* CSS decides which icon shows, so server and client render the same markup. */}
        <Sun className="size-5 dark:hidden" aria-hidden />
        <Moon className="hidden size-5 dark:block" aria-hidden />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-44">
        {OPTIONS.map(({ value, icon: Icon, ...label }) => (
          <DropdownMenuItem key={value} onClick={() => setTheme(value)} className="min-h-10 gap-2">
            <Icon className="size-4" aria-hidden />
            <span className="flex-1">{label[l]}</span>
            {theme === value && <Check className="size-4" aria-hidden />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
