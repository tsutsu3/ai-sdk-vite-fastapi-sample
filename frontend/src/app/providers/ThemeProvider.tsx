import { createContext, useContext, useEffect } from "react";
import { useAppStore, type ThemeMode, type PaletteMode } from "@/store/app-store";

type ThemeProviderProps = {
  children: React.ReactNode;
};

type ThemeProviderState = {
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  palette: PaletteMode;
  setPalette: (palette: PaletteMode) => void;
};

const initialState: ThemeProviderState = {
  theme: "system",
  setTheme: () => null,
  palette: "default",
  setPalette: () => null,
};

const ThemeProviderContext = createContext<ThemeProviderState>(initialState);

export function ThemeProvider({
  children,
  ...props
}: ThemeProviderProps) {
  const theme = useAppStore((state) => state.theme);
  const setTheme = useAppStore((state) => state.setTheme);
  const palette = useAppStore((state) => state.palette);
  const setPalette = useAppStore((state) => state.setPalette);

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

  const value = { theme, setTheme, palette, setPalette };

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  );
}

export const useTheme = () => {
  const context = useContext(ThemeProviderContext);

  if (context === undefined)
    throw new Error("useTheme must be used within a ThemeProvider");

  return context;
};
