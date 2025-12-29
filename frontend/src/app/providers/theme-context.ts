import { createContext } from "react";
import type { ThemeMode, PaletteMode } from "@/shared/types/theme";

export type ThemeProviderState = {
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

export const ThemeProviderContext =
  createContext<ThemeProviderState>(initialState);
