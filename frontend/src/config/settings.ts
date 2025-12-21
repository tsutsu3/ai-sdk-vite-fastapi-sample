import { Database, Settings } from "lucide-react";
import type { SettingsNavItem, SettingsOption } from "@/types/settings";

/**
 * Language options available in the settings dialog.
 */
export const languageOptions: SettingsOption[] = [
  { value: "en", label: "English" },
  { value: "ja", label: "日本語" },
];

/**
 * Theme options available in the settings dialog.
 */
export const themeOptions: SettingsOption[] = [
  { value: "system", label: "system" },
  { value: "light", label: "light" },
  { value: "dark", label: "dark" },
];

/**
 * Palette options available in the settings dialog.
 */
export const paletteOptions: SettingsOption[] = [
  { value: "default", label: "default" },
  { value: "warm", label: "warm" },
  { value: "cool", label: "cool" },
  { value: "mint", label: "mint" },
];

/**
 * Navigation items for the settings dialog sidebar.
 */
export const settingsNavItems: SettingsNavItem[] = [
  { id: "general", number: 1, icon: Settings },
  { id: "dataControl", number: 2, icon: Database },
];