import { type LucideIcon } from "lucide-react";

/**
 * Top-level navigation item shown in the primary sidebar.
 */
export type NavMainItem = {
  /** Stable identifier for routing and selection. */
  id: string;
  /** Route for the entry. */
  url: string;
  /** Icon component displayed in the sidebar. */
  icon: LucideIcon;
};

/**
 * Navigation group for tool sections.
 */
export type NavToolGroup = {
  /** Tool group identifier. */
  id: string;
  /** Base URL for the group. */
  url: string;
  /** Icon component for the group. */
  icon: LucideIcon;
  /** Whether the group is currently active. */
  isActive?: boolean;
  /** Optional tool entries. */
  items?: {
    /** Tool identifier. */
    id: string;
    /** Route for the tool. */
    url: string;
  }[];
};

/**
 * Tool group definition returned from the backend.
 *
 * Used to build the sidebar tool navigation and determine which tools a user
 * can access in the UI.
 */
export type ToolGroupDefinition = {
  /** Tool group identifier. */
  id: string;
  items?: {
    /** Tool identifier. */
    id: string;
  }[];
};
