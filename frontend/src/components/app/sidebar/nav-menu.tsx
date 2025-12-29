import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Link } from "react-router";
import type { NavMainItem } from "@/shared/types/ui";

export type NavMenuViewModel = {
  label?: string;
  items: NavMainItem[];
  t: (key: string) => string;
};

export type NavMenuProps = {
  viewModel: NavMenuViewModel;
};

export const NavMenu = ({ viewModel }: NavMenuProps) => {
  const { label, items, t } = viewModel;

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
};
