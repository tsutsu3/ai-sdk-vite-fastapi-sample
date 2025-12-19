import type { LucideIcon } from "lucide-react";

/**
 * Option entry used by select controls in settings.
 */
export type SettingsOption = {
  value: string;
  label: string;
};

/**
 * Sidebar entry for the settings dialog navigation.
 */
export type SettingsNavItem = {
  id: string;
  number: number;
  icon: LucideIcon;
};