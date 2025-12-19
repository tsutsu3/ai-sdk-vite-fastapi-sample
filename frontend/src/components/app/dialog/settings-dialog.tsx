import * as React from "react";
import { Database, Settings, type LucideIcon } from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
} from "@/components/ui/sidebar";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTheme } from "@/app/providers/ThemeProvider";
import { useTranslation } from "react-i18next";

const languages = [
  { code: "en", name: "English" },
  { code: "ja", name: "日本語" },
];

const themes = ["system", "light", "dark"];

function GeneralSettings() {
  const { i18n, t } = useTranslation();
  const { theme, setTheme } = useTheme();

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <label className="text-sm font-medium" htmlFor="language-select">
          {t("language")}
        </label>
        <div className="min-w-[180px] flex-1 sm:max-w-[240px]">
          <Select
            onValueChange={(value) => {
              i18n.changeLanguage(value);
              localStorage.setItem("language", value);
            }}
            value={i18n.language}
          >
            <SelectTrigger className="w-full" id="language-select">
              <SelectValue placeholder="Select language" />
            </SelectTrigger>
            <SelectContent>
              {languages.map((lang) => (
                <SelectItem key={lang.code} value={lang.code}>
                  {lang.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <label className="text-sm font-medium" htmlFor="theme-select">
          {t("theme")}
        </label>
        <div className="min-w-[180px] flex-1 sm:max-w-[240px]">
          <Select onValueChange={setTheme} value={theme}>
            <SelectTrigger className="w-full" id="theme-select">
              <SelectValue placeholder="Select theme" />
            </SelectTrigger>
            <SelectContent>
              {themes.map((theme) => (
                <SelectItem key={theme} value={theme}>
                  {t(theme)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}

function DataControlSettings() {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium">Data Control</h3>
      <p className="text-sm text-muted-foreground">
        Data control and privacy related settings.
      </p>
    </div>
  );
}

type SettingsNavItem = {
  id: string;
  number?: number;
  icon: LucideIcon;
};

const NAV_ITEMS: SettingsNavItem[] = [
  {
    id: "general",
    number: 1,
    icon: Settings,
  },
  {
    id: "dataControl",
    number: 2,
    icon: Database,
  },
];

export function SettingsDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [activeNumber, setActiveNumber] =
    React.useState<SettingsNavItem["number"]>(1);
  const { t } = useTranslation();

  const activeItem = NAV_ITEMS.find((item) => item.number === activeNumber);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="overflow-hidden p-0 md:max-h-[500px] md:max-w-[800px]">
        <DialogTitle className="sr-only">{t("settings")}</DialogTitle>
        <DialogDescription className="sr-only">
          Manage application settings
        </DialogDescription>
        <SidebarProvider className="items-start">
          {/* ===== left sidebar ===== */}
          <Sidebar collapsible="none" className="w-48 max-md:w-12">
            <SidebarContent>
              <SidebarGroup>
                <SidebarGroupContent className="pt-12">
                  <SidebarMenu>
                    {NAV_ITEMS.map((item) => (
                      <SidebarMenuItem key={item.id}>
                        <SidebarMenuButton
                          isActive={item.number === activeNumber}
                          onClick={() => setActiveNumber(item.number)}
                        >
                          <item.icon />
                          <span>{t(item.id)}</span>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            </SidebarContent>
          </Sidebar>

          {/* ===== right content ===== */}
          <main className="flex h-[480px] flex-1 flex-col overflow-hidden">
            {/* header: selected menu name */}
            <header className="flex h-16 shrink-0 items-center px-4 ">
              <div className="w-full items-center border-b">
                <h2 className="text-lg font-semibold pb-2">
                  {t(activeItem?.id || "")}
                </h2>
              </div>
            </header>

            {/* content switch */}
            <div className="flex flex-1 flex-col overflow-y-auto p-4 pt-0">
              {activeNumber === 1 && <GeneralSettings />}
              {activeNumber === 2 && <DataControlSettings />}
            </div>
          </main>
        </SidebarProvider>
      </DialogContent>
    </Dialog>
  );
}
