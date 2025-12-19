import type { ComponentProps } from "react";
import { Command } from "lucide-react";

import { NavNestedMenu } from "@/components/app/sidebar/nav-nested-menu";
import { NavUser } from "@/components/app/sidebar/nav-user";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { NavMenu } from "./nav-menu";
import { NavHistoryMenu } from "./nav-history-menu";
import { Separator } from "@radix-ui/react-separator";
import { Link } from "react-router";
import { navMainItems, navLinkGroups } from "@/config/navigation";
import { useTranslation } from "react-i18next";
import { useSidebarData } from "@/hooks/use-sidebar-data";

export function AppSidebar({ ...props }: ComponentProps<typeof Sidebar>) {
  const { authz, history, visibleToolGroups, user } = useSidebarData();
  const { t } = useTranslation();

  return (
    <Sidebar {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link to="/" className="flex items-center gap-2">
                <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                  <Command className="size-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-medium">Acme Inc</span>
                  <span className="truncate text-xs">Enterprise</span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMenu items={navMainItems} />
        <NavNestedMenu
          label={t("tools")}
          items={visibleToolGroups}
          isLoading={authz.status === "loading"}
        />
        <Separator className="mt-2" />
        <NavHistoryMenu label={t("history")} items={history.items} />
        <Separator className="mt-2" />
        <NavNestedMenu
          label={t("links")}
          items={navLinkGroups}
          className="mt-auto"
        />
        <Separator className="mt-2" />
      </SidebarContent>
      <Separator className="h-px bg-sidebar-border" />
      <SidebarFooter>
        <NavUser user={user} />
      </SidebarFooter>
    </Sidebar>
  );
}
