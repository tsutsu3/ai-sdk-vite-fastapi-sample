"use client";

import { Archive, MoreHorizontal, Trash2 } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Link } from "react-router";
import { useTranslation } from "react-i18next";
import type { HistoryItem } from "@/types/history";

export function NavHistoryMenu({
  label,
  items,
}: {
  label?: string;
  items: HistoryItem[];
}) {
  const { isMobile } = useSidebar();
  const { t } = useTranslation();

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden flex flex-col min-h-0 ">
      {label && <SidebarGroupLabel>{label}</SidebarGroupLabel>}

      <div className="flex-1 overflow-y-auto">
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.name}>
              <Tooltip delayDuration={500}>
                <TooltipTrigger asChild>
                  <SidebarMenuButton asChild>
                    <Link to={item.url} className="flex-1">
                      <span>{item.name}</span>
                    </Link>
                  </SidebarMenuButton>
                </TooltipTrigger>
                <TooltipContent>
                  <div className="flex flex-col gap-1">
                    <span>{item.name}</span>
                    <span>Updated: {item.updatedAt}</span>
                  </div>
                </TooltipContent>
              </Tooltip>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuAction showOnHover>
                    <MoreHorizontal />
                    <span className="sr-only">More</span>
                  </SidebarMenuAction>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  className="w-48"
                  side={isMobile ? "bottom" : "right"}
                  align={isMobile ? "end" : "start"}
                >
                  <DropdownMenuItem>
                    <Archive className="text-muted-foreground" />
                    <span>{t("archive")}</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Trash2 className="text-destructive" />
                    <span className="text-destructive">{t("delete")}</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </div>
    </SidebarGroup>
  );
}
