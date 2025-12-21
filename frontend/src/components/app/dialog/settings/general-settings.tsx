import type { SettingsOption } from "@/types/settings";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type GeneralSettingsProps = {
  languageOptions: SettingsOption[];
  themeOptions: SettingsOption[];
  paletteOptions: SettingsOption[];
  selectedLanguage: string;
  selectedTheme: string;
  selectedPalette: string;
  onLanguageChange: (value: string) => void;
  onThemeChange: (value: string) => void;
  onPaletteChange: (value: string) => void;
  t: (key: string) => string;
};

export function GeneralSettings({
  languageOptions,
  themeOptions,
  paletteOptions,
  selectedLanguage,
  selectedTheme,
  selectedPalette,
  onLanguageChange,
  onThemeChange,
  onPaletteChange,
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
      <div className="flex flex-wrap items-center justify-between gap-3">
        <label className="text-sm font-medium" htmlFor="palette-select">
          {t("palette")}
        </label>
        <div className="min-w-45 flex-1 sm:max-w-60">
          <Select onValueChange={onPaletteChange} value={selectedPalette}>
            <SelectTrigger className="w-full" id="palette-select">
              <SelectValue placeholder="Select palette" />
            </SelectTrigger>
            <SelectContent>
              {paletteOptions.map((palette) => (
                <SelectItem key={palette.value} value={palette.value}>
                  {t(palette.label)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}
