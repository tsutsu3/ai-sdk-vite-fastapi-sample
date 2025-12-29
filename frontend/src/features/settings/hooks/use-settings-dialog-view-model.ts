import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useTheme } from "@/app/providers/use-theme";
import {
  languageOptions,
  settingsNavItems,
  themeOptions,
  paletteOptions,
} from "@/features/settings/config/settings";
import type { SettingsNavItem } from "@/features/settings/types/settings";
import type { ThemeMode, PaletteMode } from "@/shared/types/theme";
import { useDataControlSettingsViewModel } from "./use-data-control-settings-view-model";

/**
 * Provides state and handlers for the settings dialog flow.
 */
export const useSettingsDialogViewModel = () => {
  const [activeNumber, setActiveNumber] =
    useState<SettingsNavItem["number"]>(1);
  const { i18n, t } = useTranslation();
  const { theme, setTheme } = useTheme();
  const { palette, setPalette } = useTheme();
  const dataControl = useDataControlSettingsViewModel();

  const activeItem = useMemo(
    () => settingsNavItems.find((item) => item.number === activeNumber),
    [activeNumber],
  );

  const handleLanguageChange = useCallback(
    (value: string) => {
      i18n.changeLanguage(value);
      localStorage.setItem("language", value);
    },
    [i18n],
  );

  const handleThemeChange = useCallback(
    (value: string) => {
      setTheme(value as ThemeMode);
    },
    [setTheme],
  );

  const handlePaletteChange = useCallback(
    (value: string) => {
      setPalette(value as PaletteMode);
    },
    [setPalette],
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
    dataControl,
  };
};
