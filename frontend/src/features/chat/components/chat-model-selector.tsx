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
import { Button } from "@/components/ui/button";
import type { ChatModelSelectorViewModel } from "@/features/chat/hooks/use-chat-view-model";

export type ChatModelSelectorProps = {
  viewModel: ChatModelSelectorViewModel;
};

export const ChatModelSelector = ({
  viewModel,
}: ChatModelSelectorProps) => {
  const {
    selectedModelId,
    selectedModelName,
    selectedModelChefSlug,
    groups,
    onSelectModel,
    open,
    onOpenChange,
    t,
  } = viewModel;

  return (
    <ModelSelector onOpenChange={onOpenChange} open={open}>
      <ModelSelectorTrigger asChild>
        <Button className="w-50 justify-between" variant="outline">
          {selectedModelChefSlug && (
            <ModelSelectorLogo provider={selectedModelChefSlug} />
          )}
          {selectedModelName ? (
            <ModelSelectorName>{selectedModelName}</ModelSelectorName>
          ) : (
            <ModelSelectorName>Select model</ModelSelectorName>
          )}
        </Button>
      </ModelSelectorTrigger>
      <ModelSelectorContent>
        <ModelSelectorInput placeholder={t("searchModels")} />
        <ModelSelectorList>
          <ModelSelectorEmpty>No models found.</ModelSelectorEmpty>
          {groups.map((group) => (
            <ModelSelectorGroup heading={group.chef} key={group.chef}>
              {group.models.map((model) => (
                <ModelSelectorItem
                  key={model.id}
                  onSelect={() => onSelectModel(model.id)}
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
