import type { SettingsOption } from "@/types/settings";
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
import { useSettingsDialog } from "@/hooks/use-settings-dialog";

type GeneralSettingsProps = {
  languageOptions: SettingsOption[];
  themeOptions: SettingsOption[];
  selectedLanguage: string;
  selectedTheme: string;
  onLanguageChange: (value: string) => void;
  onThemeChange: (value: string) => void;
  t: (key: string) => string;
};

/**
 * Displays the general settings section UI.
 */
function GeneralSettings({
  languageOptions,
  themeOptions,
  selectedLanguage,
  selectedTheme,
  onLanguageChange,
  onThemeChange,
  t,
}: GeneralSettingsProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <label className="text-sm font-medium" htmlFor="language-select">
          {t("language")}
        </label>
        <div className="min-w-45 flex-1 sm:max-w-60">
          <Select onValueChange={onLanguageChange} value={selectedLanguage}>
            <SelectTrigger className="w-full" id="language-select">
              <SelectValue placeholder="Select language" />
            </SelectTrigger>
            <SelectContent>
              {languageOptions.map((lang) => (
                <SelectItem key={lang.value} value={lang.value}>
                  {lang.label}
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
        <div className="min-w-45 flex-1 sm:max-w-60">
          <Select onValueChange={onThemeChange} value={selectedTheme}>
            <SelectTrigger className="w-full" id="theme-select">
              <SelectValue placeholder="Select theme" />
            </SelectTrigger>
            <SelectContent>
              {themeOptions.map((theme) => (
                <SelectItem key={theme.value} value={theme.value}>
                  {t(theme.label)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}

/**
 * Placeholder UI for data control settings.
 */
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

export function SettingsDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const {
    activeNumber,
    activeItem,
    t,
    languageOptions,
    themeOptions,
    selectedLanguage,
    selectedTheme,
    settingsNavItems,
    onActiveNumberChange,
    onLanguageChange,
    onThemeChange,
  } = useSettingsDialog();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="overflow-hidden p-0 md:max-h-125 md:max-w-200">
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
                    {settingsNavItems.map((item) => (
                      <SidebarMenuItem key={item.id}>
                        <SidebarMenuButton
                          isActive={item.number === activeNumber}
                          onClick={() => onActiveNumberChange(item.number)}
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
          <main className="flex h-120 flex-1 flex-col overflow-hidden">
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
              {activeNumber === 1 && (
                <GeneralSettings
                  languageOptions={languageOptions}
                  themeOptions={themeOptions}
                  selectedLanguage={selectedLanguage}
                  selectedTheme={selectedTheme}
                  onLanguageChange={onLanguageChange}
                  onThemeChange={onThemeChange}
                  t={t}
                />
              )}
              {activeNumber === 2 && <DataControlSettings />}
            </div>
          </main>
        </SidebarProvider>
      </DialogContent>
    </Dialog>
  );
}