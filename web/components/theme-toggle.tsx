"use client";

import { useSyncExternalStore } from "react";
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getServerTheme, getTheme, setTheme, subscribeTheme } from "@/lib/theme";

export function ThemeToggle({ label }: { label: string }) {
  const theme = useSyncExternalStore(subscribeTheme, getTheme, getServerTheme);

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={label}
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
    >
      {theme === "dark" ? <Moon size={18} /> : <Sun size={18} />}
    </Button>
  );
}
