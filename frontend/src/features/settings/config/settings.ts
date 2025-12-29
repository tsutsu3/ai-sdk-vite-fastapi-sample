import { Database, Settings } from "lucide-react";
import type {
  SettingsNavItem,
  SettingsOption,
} from "@/features/settings/types/settings";

/**
 * Language options available in the settings dialog.
 *
 * Changing this value updates the i18n language and persists it in local storage.
 */
export const languageOptions: SettingsOption[] = [
  { value: "en", label: "English" },
  { value: "ja", label: "日本語" },
];

/**
 * Theme options available in the settings dialog.
 *
 * Changing this value updates the app theme provider immediately.
 */
export const themeOptions: SettingsOption[] = [
  { value: "system", label: "system" },
  { value: "light", label: "light" },
  { value: "dark", label: "dark" },
];

/**
 * Palette options available in the settings dialog.
 *
 * Palette changes affect UI accent colors across the shell.
 */
export const paletteOptions: SettingsOption[] = [
  { value: "default", label: "default" },
  { value: "warm", label: "warm" },
  { value: "cool", label: "cool" },
  { value: "mint", label: "mint" },
];

/**
 * Navigation items for the settings dialog sidebar.
 *
 * These entries must stay in sync with the settings panel layout.
 */
export const settingsNavItems: SettingsNavItem[] = [
  { id: "general", number: 1, icon: Settings },
  { id: "dataControl", number: 2, icon: Database },
];
