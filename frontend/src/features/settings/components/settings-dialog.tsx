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
import { cn } from "@/lib/utils";
import { GeneralSettings } from "@/features/settings/components/general-settings";
import { DataControlSettingsView } from "@/features/settings/components/data-control-settings";
import type { useSettingsDialogViewModel } from "@/features/settings/hooks/use-settings-dialog-view-model";

export type SettingsDialogViewModel = ReturnType<
  typeof useSettingsDialogViewModel
>;

export type SettingsDialogViewProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  viewModel: SettingsDialogViewModel;
};

export const SettingsDialogView = ({
  open,
  onOpenChange,
  viewModel,
}: SettingsDialogViewProps) => {
  const {
    activeNumber,
    activeItem,
    t,
    languageOptions,
    themeOptions,
    paletteOptions,
    selectedLanguage,
    selectedTheme,
    selectedPalette,
    settingsNavItems,
    onActiveNumberChange,
    onLanguageChange,
    onThemeChange,
    onPaletteChange,
    dataControl,
  } = viewModel;

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
                          className={cn(
                            "data-[active=true]:bg-primary data-[active=true]:text-primary-foreground",
                          )}
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
            <header className="flex h-16 shrink-0 items-center px-4">
              <div className="w-full items-center border-b">
                <h2 className="pb-2 text-lg font-semibold">
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
                  paletteOptions={paletteOptions}
                  selectedLanguage={selectedLanguage}
                  selectedTheme={selectedTheme}
                  selectedPalette={selectedPalette}
                  onLanguageChange={onLanguageChange}
                  onThemeChange={onThemeChange}
                  onPaletteChange={onPaletteChange}
                  t={t}
                />
              )}
              {activeNumber === 2 && (
                <DataControlSettingsView viewModel={dataControl} />
              )}
            </div>
          </main>
        </SidebarProvider>
      </DialogContent>
    </Dialog>
  );
};
