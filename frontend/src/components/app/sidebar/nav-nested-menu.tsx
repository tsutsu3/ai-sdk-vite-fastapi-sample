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
import { useAppStore } from "@/store/app-store";
import { useTranslation } from "react-i18next";
import { type NavToolGroup } from "@/types/ui";

export function NavNestedMenu({
  items,
  label,
  isLoading,
  ...props
}: {
  label: string;
  items: NavToolGroup[];
  isLoading?: boolean;
} & React.ComponentPropsWithoutRef<typeof SidebarGroup>) {
  const activeToolIds = useAppStore((state) => state.activeToolIds);
  const addActiveToolId = useAppStore((state) => state.addActiveToolId);
  const removeActiveToolId = useAppStore((state) => state.removeActiveToolId);
  const { t } = useTranslation();

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
        {items.map((item) => (
          <Collapsible
            key={item.id}
            asChild
            defaultOpen={
              item.id ? activeToolIds.includes(item.id) : Boolean(item.isActive)
            }
            open={
              item.id ? activeToolIds.includes(item.id) : Boolean(item.isActive)
            }
            onOpenChange={(open) => {
              if (!item.id) return;
              if (open) {
                addActiveToolId(item.id);
              } else {
                removeActiveToolId(item.id);
              }
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
              <CollapsibleContent>
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
        ))}
      </SidebarMenu>
    </SidebarGroup>
  );
}
