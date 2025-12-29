import { useAppStore } from "@/store/app-store";
import { useThemeSync } from "@/shared/hooks/use-theme-sync";
import { ThemeProviderContext } from "@/app/providers/theme-context";

type ThemeProviderProps = {
  children: React.ReactNode;
};

export const ThemeProvider = ({ children, ...props }: ThemeProviderProps) => {
  const theme = useAppStore((state) => state.theme);
  const setTheme = useAppStore((state) => state.setTheme);
  const palette = useAppStore((state) => state.palette);
  const setPalette = useAppStore((state) => state.setPalette);

  useThemeSync({ theme, palette });

  const value = { theme, setTheme, palette, setPalette };

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  );
};
