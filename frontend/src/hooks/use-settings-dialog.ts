import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useTheme } from "@/app/providers/ThemeProvider";
import { languageOptions, settingsNavItems, themeOptions, paletteOptions } from "@/config/settings";
import type { SettingsNavItem } from "@/types/settings";
import type { ThemeMode } from "@/store/app-store";
import type { PaletteMode } from "@/store/app-store";

/**
 * Provides state and handlers for the settings dialog.
 */
export const useSettingsDialog = () => {
  const [activeNumber, setActiveNumber] = useState<SettingsNavItem["number"]>(1);
  const { i18n, t } = useTranslation();
  const { theme, setTheme } = useTheme();
  const { palette, setPalette } = useTheme();

  const activeItem = useMemo(
    () => settingsNavItems.find((item) => item.number === activeNumber),
    [activeNumber]
  );

  const handleLanguageChange = useCallback(
    (value: string) => {
      i18n.changeLanguage(value);
      localStorage.setItem("language", value);
    },
    [i18n]
  );

  const handleThemeChange = useCallback(
    (value: string) => {
      setTheme(value as ThemeMode);
    },
    [setTheme]
  );

  const handlePaletteChange = useCallback(
    (value: string) => {
      setPalette(value as PaletteMode);
    },
    [setPalette]
  );

  return {
    activeNumber,
    activeItem,
    t,
    languageOptions,
    themeOptions,
    paletteOptions,
    selectedLanguage: i18n.language,
    selectedTheme: theme,
    selectedPalette: palette,
    settingsNavItems,
    onActiveNumberChange: setActiveNumber,
    onLanguageChange: handleLanguageChange,
    onThemeChange: handleThemeChange,
    onPaletteChange: handlePaletteChange,
  };
};
