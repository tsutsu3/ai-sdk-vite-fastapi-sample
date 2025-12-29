import { SlidersHorizontalIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type { ChatAdvancedSettingsViewModel } from "@/features/chat/hooks/use-chat-view-model";

export type ChatAdvancedSettingsPopoverProps = {
  viewModel: ChatAdvancedSettingsViewModel;
};

export const ChatAdvancedSettingsPopover = ({
  viewModel,
}: ChatAdvancedSettingsPopoverProps) => {
  const {
    t,
    temperature,
    topP,
    defaultTemperature,
    defaultTopP,
    onTemperatureChange,
    onTopPChange,
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
        </div>
      </PopoverContent>
    </Popover>
  );
};
