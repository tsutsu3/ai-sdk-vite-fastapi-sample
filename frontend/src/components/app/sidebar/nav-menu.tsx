"use client";

import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Link } from "react-router";
import { useTranslation } from "react-i18next";
import type { NavMainItem } from "@/types/ui";

export function NavMenu({
  label,
  items,
}: {
  label?: string;
  items: NavMainItem[];
}) {
  const { t } = useTranslation();

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      {label && <SidebarGroupLabel>{label}</SidebarGroupLabel>}
      <SidebarMenu>
        {items.map((item) => (
          <SidebarMenuItem key={item.id}>
            <SidebarMenuButton asChild>
              <Link to={item.url}>
                <item.icon />
                <span>{t(item.id)}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  );
}
