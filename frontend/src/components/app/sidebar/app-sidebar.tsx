import type { ComponentProps } from "react";
import { Command } from "lucide-react";

import { NavNestedMenu } from "@/components/app/sidebar/nav-nested-menu";
import { NavUser, type NavUserViewModel } from "@/components/app/sidebar/nav-user";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { NavMenu, type NavMenuViewModel } from "./nav-menu";
import { NavHistoryMenu, type NavHistoryMenuViewModel } from "./nav-history-menu";
import { Separator } from "@radix-ui/react-separator";
import { Link } from "react-router";
import type { NavNestedMenuViewModel } from "@/components/app/sidebar/nav-nested-menu";

export type AppSidebarViewModel = ComponentProps<typeof Sidebar> & {
  mainMenu: NavMenuViewModel;
  toolMenu: NavNestedMenuViewModel;
  historyMenu: NavHistoryMenuViewModel;
  linkMenu: NavNestedMenuViewModel;
  userMenu: NavUserViewModel;
};

export type AppSidebarProps = {
  viewModel: AppSidebarViewModel;
};

export const AppSidebar = ({ viewModel }: AppSidebarProps) => {
  const {
    mainMenu,
    toolMenu,
    linkMenu,
    historyMenu,
    userMenu,
    ...props
  } = viewModel;

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
        <NavMenu viewModel={mainMenu} />
        <NavNestedMenu viewModel={toolMenu} />
        <Separator className="mt-2" />
        <NavHistoryMenu viewModel={historyMenu} />
        <Separator className="mt-2" />
        <NavNestedMenu viewModel={linkMenu} />
        <Separator className="mt-2" />
      </SidebarContent>
      <Separator className="bg-sidebar-border h-px" />
      <SidebarFooter>
        <NavUser viewModel={userMenu} />
      </SidebarFooter>
    </Sidebar>
  );
};
