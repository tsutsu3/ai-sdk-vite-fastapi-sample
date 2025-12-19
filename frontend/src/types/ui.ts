import { type LucideIcon } from "lucide-react";

export type NavMainItem = {
  id: string;
  url: string;
  icon: LucideIcon;
};

export type NavToolGroup = {
  id: string;
  url: string;
  icon: LucideIcon;
  isActive?: boolean;
  items?: {
    id: string;
    url: string;
  }[];
};
