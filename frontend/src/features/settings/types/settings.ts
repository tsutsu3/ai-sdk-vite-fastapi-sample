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

/**
 * Archived conversation metadata used by data control settings.
 *
 * The data control screen uses this shape to populate the archive list and
 * provide timestamps for sorting.
 */
export type ArchivedConversation = {
  id: string;
  title: string;
  updatedAt: string;
  createdAt?: string | null;
};
