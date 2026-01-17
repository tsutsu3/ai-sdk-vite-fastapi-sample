import { SlidersHorizontalIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type { ToolsAdvancedSettingsViewModel } from "@/features/tools/hooks/tools-view-model-types";

export type ToolsAdvancedSettingsPopoverProps = {
  viewModel: ToolsAdvancedSettingsViewModel;
};

export const ToolsAdvancedSettingsPopover = ({
  viewModel,
}: ToolsAdvancedSettingsPopoverProps) => {
  const {
    t,
    temperature,
    topP,
    hydeEnabled,
    maxDocuments,
    injectedPrompt,
    defaultTemperature,
    defaultTopP,
    defaultHydeEnabled,
    defaultMaxDocuments,
    onTemperatureChange,
    onTopPChange,
    onHydeToggle,
    onMaxDocumentsChange,
    onInjectedPromptChange,
  } = viewModel;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button type="button" variant="ghost" size="sm">
          <SlidersHorizontalIcon className="mr-2 size-4" />
          {t("advanced")}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" side="top" sideOffset={8}>
        <div className="text-muted-foreground mb-2 pb-2 text-sm font-medium">
          {t("advanced")}
        </div>
        <div className="grid gap-6">
          <label className="text-muted-foreground grid gap-1 text-xs">
            <div className="flex items-center justify-between">
              <span>
                {t("temperature")} ({t("defaultValue", { value: defaultTemperature })})
              </span>
              <span className="text-foreground">{temperature[0] ?? 1}</span>
            </div>
            <Slider
              value={temperature}
              onValueChange={onTemperatureChange}
              min={0}
              max={2}
              step={0.1}
            />
          </label>
          <label className="text-muted-foreground grid gap-1 text-xs">
            <div className="flex items-center justify-between">
              <span>
                {t("topP")} ({t("defaultValue", { value: defaultTopP })})
              </span>
              <span className="text-foreground">{topP[0] ?? 1}</span>
            </div>
            <Slider
              value={topP}
              onValueChange={onTopPChange}
              min={0}
              max={1}
              step={0.01}
            />
          </label>
          <div className="text-muted-foreground grid gap-2 text-xs">
            <div className="flex items-center justify-between">
              <span>
                {t("hyde")} ({t("defaultValue", { value: defaultHydeEnabled ? "on" : "off" })})
              </span>
              <span className="text-foreground">
                {hydeEnabled ? t("on") : t("off")}
              </span>
            </div>
            <Button
              onClick={onHydeToggle}
              type="button"
              variant={hydeEnabled ? "default" : "outline"}
            >
              {hydeEnabled ? t("hydeEnabled") : t("hydeDisabled")}
            </Button>
          </div>
          <label className="text-muted-foreground grid gap-1 text-xs">
            <div className="flex items-center justify-between">
              <span>
                {t("maxDocuments")} ({t("defaultValue", { value: defaultMaxDocuments })})
              </span>
              <span className="text-foreground">{maxDocuments[0] ?? 0}</span>
            </div>
            <Slider
              value={maxDocuments}
              onValueChange={onMaxDocumentsChange}
              min={1}
              max={20}
              step={1}
            />
          </label>
          <label className="text-muted-foreground grid gap-1 text-xs">
            <span>{t("injectedPrompt")}</span>
            <Textarea
              value={injectedPrompt}
              onChange={(event) => onInjectedPromptChange(event.target.value)}
              placeholder={t("injectedPromptPlaceholder")}
              rows={3}
            />
          </label>
        </div>
      </PopoverContent>
    </Popover>
  );
};
