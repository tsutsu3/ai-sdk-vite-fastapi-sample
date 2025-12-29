import { useEffect } from "react";
import type { ThemeMode, PaletteMode } from "@/shared/types/theme";

type UseThemeSyncArgs = {
  theme: ThemeMode;
  palette: PaletteMode;
};

export const useThemeSync = ({ theme, palette }: UseThemeSyncArgs) => {
  useEffect(() => {
    const root = window.document.documentElement;

    root.classList.remove("light", "dark");

    const resolvedTheme =
      theme === "system"
        ? window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light"
        : theme;

    root.classList.add(resolvedTheme);
  }, [theme]);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("theme-warm", "theme-cool", "theme-mint");
    root.classList.add(`theme-${palette}`);
  }, [palette]);
};
