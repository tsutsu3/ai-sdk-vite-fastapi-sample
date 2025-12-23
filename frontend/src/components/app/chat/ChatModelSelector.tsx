import { CheckIcon } from "lucide-react";
import {
  ModelSelector,
  ModelSelectorContent,
  ModelSelectorEmpty,
  ModelSelectorGroup,
  ModelSelectorInput,
  ModelSelectorItem,
  ModelSelectorList,
  ModelSelectorLogo,
  ModelSelectorLogoGroup,
  ModelSelectorName,
  ModelSelectorTrigger,
} from "@/components/ai-elements/model-selector";
import { useMemo, useState } from "react";
import type { ChatModel } from "@/types/chat";
import { Button } from "@/components/ui/button";
import { useTranslation } from "react-i18next";

export type ChatModelSelectorProps = {
  models: ChatModel[];
  selectedModelId: string;
  onModelChange: (modelId: string) => void;
};

export const ChatModelSelector = ({
  models,
  selectedModelId,
  onModelChange,
}: ChatModelSelectorProps) => {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const selectedModelData = useMemo(
    () => models.find((model) => model.id === selectedModelId),
    [models, selectedModelId]
  );
  const chefs = useMemo(
    () => Array.from(new Set(models.map((model) => model.chef))),
    [models]
  );

  return (
    <ModelSelector onOpenChange={setOpen} open={open}>
      <ModelSelectorTrigger asChild>
        <Button className="w-50 justify-between" variant="outline">
          {selectedModelData?.chefSlug && (
            <ModelSelectorLogo provider={selectedModelData.chefSlug} />
          )}
          {selectedModelData?.name ? (
            <ModelSelectorName>{selectedModelData.name}</ModelSelectorName>
          ) : (
            <ModelSelectorName>Select model</ModelSelectorName>
          )}
        </Button>
      </ModelSelectorTrigger>
      <ModelSelectorContent>
        <ModelSelectorInput placeholder={t("searchModels")} />
        <ModelSelectorList>
          <ModelSelectorEmpty>No models found.</ModelSelectorEmpty>
          {chefs.map((chef) => (
            <ModelSelectorGroup heading={chef} key={chef}>
              {models
                .filter((model) => model.chef === chef)
                .map((model) => (
                  <ModelSelectorItem
                    key={model.id}
                    onSelect={() => {
                      onModelChange(model.id);
                      setOpen(false);
                    }}
                    value={model.id}
                  >
                    <ModelSelectorLogo provider={model.chefSlug} />
                    <ModelSelectorName>{model.name}</ModelSelectorName>
                    <ModelSelectorLogoGroup>
                      {model.providers.map((provider) => (
                        <ModelSelectorLogo key={provider} provider={provider} />
                      ))}
                    </ModelSelectorLogoGroup>
                    {selectedModelId === model.id ? (
                      <CheckIcon className="ml-auto size-4" />
                    ) : (
                      <div className="ml-auto size-4" />
                    )}
                  </ModelSelectorItem>
                ))}
            </ModelSelectorGroup>
          ))}
        </ModelSelectorList>
      </ModelSelectorContent>
    </ModelSelector>
  );
};
