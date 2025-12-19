import { Settings, ChevronsUpDown, CreditCard, LogOut } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { useState } from "react";
import { SettingsDialog } from "../dialog/settings-dialog";
import Avatar from "boring-avatars";
import { Skeleton } from "@/components/ui/skeleton";
import { useAppStore } from "@/store/app-store";
import { useTranslation } from "react-i18next";
import { monotoneAvatarColors } from "@/config/avatar";

export function NavUser({
  user,
}: {
  user: {
    name: string;
    email: string;
    avatar?: string;
  };
}) {
  const { isMobile } = useSidebar();
  const [showSettings, setShowSettings] = useState(false);
  const authz = useAppStore((state) => state.authz);
  const avatarName = user.name || user.email || undefined;
  const { t } = useTranslation();

  return (
    <>
      <SidebarMenu>
        <SidebarMenuItem>
          {authz.status === "loading" ? (
            <SidebarMenuButton size="lg">
              <div className="h-8 w-8 rounded-lg overflow-hidden">
                <Skeleton className="h-8 w-8 rounded-lg" />
              </div>

              <div className="grid flex-1 text-left text-sm leading-tight">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-3 w-36 mt-1" />
              </div>
            </SidebarMenuButton>
          ) : (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  size="lg"
                  className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                >
                  <div className="h-8 w-8 rounded-lg overflow-hidden">
                    <Avatar
                      size={32}
                      name={avatarName}
                      variant="beam"
                      colors={monotoneAvatarColors}
                    />
                  </div>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-medium">{user.name}</span>
                    <span className="truncate text-xs">{user.email}</span>
                  </div>
                  <ChevronsUpDown className="ml-auto size-4" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
                side={isMobile ? "bottom" : "right"}
                align="end"
                sideOffset={4}
              >
                <DropdownMenuLabel className="p-0 font-normal">
                  <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                    <div className="h-8 w-8 rounded-lg overflow-hidden">
                      <Avatar
                        size={32}
                        name={avatarName}
                        variant="beam"
                        colors={monotoneAvatarColors}
                      />
                    </div>
                    <div className="grid flex-1 text-left text-sm leading-tight">
                      <span className="truncate font-medium">{user.name}</span>
                      <span className="truncate text-xs">{user.email}</span>
                    </div>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuGroup>
                  <DropdownMenuItem
                    onSelect={() => {
                      setShowSettings(true);
                    }}
                  >
                    <Settings />
                    {t("settings")}
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <CreditCard />
                    {t("billing")}
                  </DropdownMenuItem>
                </DropdownMenuGroup>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <LogOut />
                  {t("logout")}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </SidebarMenuItem>
      </SidebarMenu>

      <SettingsDialog open={showSettings} onOpenChange={setShowSettings} />
    </>
  );
}
