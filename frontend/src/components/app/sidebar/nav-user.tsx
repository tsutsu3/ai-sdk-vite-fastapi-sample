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
} from "@/components/ui/sidebar";
import {
  SettingsDialogView,
  type SettingsDialogViewModel,
} from "@/features/settings/components/settings-dialog";
import {
  BillingDialogView,
  type BillingDialogViewModel,
} from "@/features/billing/components/billing-dialog";
import Avatar from "boring-avatars";
import { Skeleton } from "@/components/ui/skeleton";
import { monotoneAvatarColors } from "@/features/navigation/config/avatar";
import type { AuthzSlice } from "@/store/app-store.types";

export type NavUserViewModel = {
  user: {
    name: string;
    email: string;
    avatar?: string;
  };
  avatarName?: string;
  authzStatus: AuthzSlice["authz"]["status"];
  settingsOpen: boolean;
  onSettingsOpenChange: (open: boolean) => void;
  billingOpen: boolean;
  onBillingOpenChange: (open: boolean) => void;
  settingsDialog: SettingsDialogViewModel;
  billingDialog: BillingDialogViewModel;
  isMobile: boolean;
  t: (key: string) => string;
};

export type NavUserProps = {
  viewModel: NavUserViewModel;
};

export const NavUser = ({ viewModel }: NavUserProps) => {
  const {
    user,
    avatarName,
    authzStatus,
    settingsOpen,
    onSettingsOpenChange,
    billingOpen,
    onBillingOpenChange,
    settingsDialog,
    billingDialog,
    isMobile,
    t,
  } = viewModel;
  const resolvedAvatarName = avatarName ?? user.name ?? user.email ?? undefined;

  return (
    <>
      <SidebarMenu>
        <SidebarMenuItem>
          {authzStatus === "loading" ? (
            <SidebarMenuButton size="lg">
              <div className="h-8 w-8 overflow-hidden rounded-lg">
                <Skeleton className="h-8 w-8 rounded-lg" />
              </div>

              <div className="grid flex-1 text-left text-sm leading-tight">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="mt-1 h-3 w-36" />
              </div>
            </SidebarMenuButton>
          ) : authzStatus === "success" ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  size="lg"
                  className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                >
                  <div className="h-8 w-8 overflow-hidden rounded-lg">
                    <Avatar
                      size={32}
                      name={resolvedAvatarName}
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
                    <div className="h-8 w-8 overflow-hidden rounded-lg">
                      <Avatar
                        size={32}
                        name={resolvedAvatarName}
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
                      onSettingsOpenChange(true);
                    }}
                  >
                    <Settings />
                    {t("settings")}
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onSelect={() => {
                      onBillingOpenChange(true);
                    }}
                  >
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
          ) : (
            <SidebarMenuButton size="lg">
            </SidebarMenuButton>
          )}
        </SidebarMenuItem>
      </SidebarMenu>

      <SettingsDialogView
        open={settingsOpen}
        onOpenChange={onSettingsOpenChange}
        viewModel={settingsDialog}
      />
      <BillingDialogView
        open={billingOpen}
        onOpenChange={onBillingOpenChange}
        viewModel={billingDialog}
      />
    </>
  );
};
