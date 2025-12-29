import { ChevronRight } from "lucide-react";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar";
import { Link } from "react-router";
import { type NavToolGroup } from "@/shared/types/ui";

export type NavNestedMenuViewModel = {
  label: string;
  items: NavToolGroup[];
  isLoading?: boolean;
  openGroupIds?: string[];
  onToggleGroup?: (groupId: string, open: boolean) => void;
  t: (key: string) => string;
} & React.ComponentPropsWithoutRef<typeof SidebarGroup>;

export type NavNestedMenuProps = {
  viewModel: NavNestedMenuViewModel;
};

export const NavNestedMenu = ({ viewModel }: NavNestedMenuProps) => {
  const {
    items,
    label,
    isLoading,
    openGroupIds = [],
    onToggleGroup,
    t,
    ...props
  } = viewModel;

  if (isLoading) {
    return (
      <SidebarGroup className="group-data-[collapsible=icon]:hidden">
        <SidebarGroupLabel>{label}</SidebarGroupLabel>
        <SidebarMenu>
          {[0, 1].map((idx) => (
            <SidebarMenuSkeleton key={idx} showIcon />
          ))}
        </SidebarMenu>
      </SidebarGroup>
    );
  }

  if (items.length === 0) {
    return null;
  }

  return (
    <SidebarGroup {...props}>
      <SidebarGroupLabel>{label}</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => {
          const isOpen = item.id
            ? openGroupIds.includes(item.id)
            : Boolean(item.isActive);
          return (
            <Collapsible
              key={item.id}
              asChild
              defaultOpen={isOpen}
              open={isOpen}
              onOpenChange={(open) => {
                if (!item.id) return;
                onToggleGroup?.(item.id, open);
              }}
            >
              <SidebarMenuItem>
                <CollapsibleTrigger asChild>
                  <SidebarMenuButton tooltip={t(item.id)}>
                    {item.icon && <item.icon />}
                    <span>{t(item.id)}</span>
                    <ChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
                  </SidebarMenuButton>
                </CollapsibleTrigger>
                <CollapsibleContent className="data-[state=open]:animate-collapsible-down data-[state=closed]:animate-collapsible-up overflow-hidden">
                  <SidebarMenuSub>
                    {item.items?.map((subItem) => (
                      <SidebarMenuSubItem key={subItem.id}>
                        <SidebarMenuSubButton asChild>
                          <Link to={subItem.url}>
                            <span>{t(subItem.id)}</span>
                          </Link>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                    ))}
                  </SidebarMenuSub>
                </CollapsibleContent>
              </SidebarMenuItem>
            </Collapsible>
          );
        })}
      </SidebarMenu>
    </SidebarGroup>
  );
};
