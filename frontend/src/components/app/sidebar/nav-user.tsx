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

const avatarColors = ["#92A1C6", "#146A7C", "#F0AB3D", "#C271B4", "#C20D90"];

function hexToRgb(hex: string) {
  const v = hex.replace("#", "");
  const r = parseInt(v.slice(0, 2), 16);
  const g = parseInt(v.slice(2, 4), 16);
  const b = parseInt(v.slice(4, 6), 16);
  return { r, g, b };
}

function rgbToHex(r: number, g: number, b: number) {
  return "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");
}

function toMonotone(hex: string, amount = 0.75): string {
  const { r, g, b } = hexToRgb(hex);

  const gray = Math.round(0.299 * r + 0.587 * g + 0.114 * b);

  const mix = (c: number) => Math.round(c * (1 - amount) + gray * amount);

  return rgbToHex(mix(r), mix(g), mix(b));
}

const monotoneAvatarColors = avatarColors.map((c) => toMonotone(c, 0.65));

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
