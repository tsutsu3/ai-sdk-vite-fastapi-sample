import { useCallback, useMemo, useState } from "react";
import { chatModels } from "@/features/chat/config/chat-models";
import type { ChatModel } from "@/features/chat/types/chat";
import { useAppStore } from "@/store/app-store";
import type {
  ChatAdvancedSettingsViewModel,
  ChatModelSelectorViewModel,
} from "@/features/chat/hooks/chat-view-model-types";

type UseChatModelSettingsViewModelArgs = {
  t: (key: string, params?: Record<string, unknown>) => string;
};

export type ChatModelSettingsViewModel = {
  models: ChatModel[];
  selectedModelId: string;
  selectedModelName: string;
  selectedModelData?: ChatModel;
  defaultWebSearchEngine: string;
  modelSelector: ChatModelSelectorViewModel;
  advancedSettings: ChatAdvancedSettingsViewModel;
};

const DEFAULT_TEMPERATURE = 1;
const DEFAULT_TOP_P = 1;

export const useChatModelSettingsViewModel = ({
  t,
}: UseChatModelSettingsViewModelArgs): ChatModelSettingsViewModel => {
  const capabilities = useAppStore((state) => state.capabilities);
  const [modelSelectorOpen, setModelSelectorOpen] = useState(false);
  const [temperature, setTemperature] = useState(DEFAULT_TEMPERATURE);
  const [topP, setTopP] = useState(DEFAULT_TOP_P);
  const [rawSelectedModelId, setRawSelectedModelId] = useState<string>("");

  const models = useMemo<ChatModel[]>(() => {
    if (capabilities.status === "success" && capabilities.models.length) {
      return capabilities.models;
    }
    return chatModels;
  }, [capabilities.status, capabilities.models]);

  const selectedModelId = useMemo(() => {
    if (!models.length) {
      return "";
    }

    if (
      rawSelectedModelId &&
      models.some((entry) => entry.id === rawSelectedModelId)
    ) {
      return rawSelectedModelId;
    }

    const preferredDefault = capabilities.defaultModel?.trim();

    if (
      preferredDefault &&
      models.some((entry) => entry.id === preferredDefault)
    ) {
      return preferredDefault;
    }

    return models[0]?.id ?? "";
  }, [models, capabilities.defaultModel, rawSelectedModelId]);

  const defaultWebSearchEngine =
    typeof capabilities.defaultWebSearchEngine === "string"
      ? capabilities.defaultWebSearchEngine
      : "";

  const selectedModelData = useMemo(
    () => models.find((entry) => entry.id === selectedModelId),
    [models, selectedModelId],
  );

  const selectedModelName = selectedModelData?.name ?? t("chat.model.unknown");

  const modelSelectorGroups = useMemo(() => {
    const chefs = Array.from(new Set(models.map((entry) => entry.chef)));
    return chefs.map((chef) => ({
      chef,
      models: models.filter((entry) => entry.chef === chef),
    }));
  }, [models]);

  const handleSelectModel = useCallback((modelId: string) => {
    setRawSelectedModelId(modelId);
    setModelSelectorOpen(false);
  }, []);

  const handleTemperatureChange = useCallback((value: number[]) => {
    setTemperature(value[0] ?? DEFAULT_TEMPERATURE);
  }, []);

  const handleTopPChange = useCallback((value: number[]) => {
    setTopP(value[0] ?? DEFAULT_TOP_P);
  }, []);

  return {
    models,
    selectedModelId,
    selectedModelName,
    selectedModelData,
    defaultWebSearchEngine,
    modelSelector: {
      t,
      open: modelSelectorOpen,
      onOpenChange: setModelSelectorOpen,
      selectedModelId,
      selectedModelName: selectedModelData?.name,
      selectedModelChefSlug: selectedModelData?.chefSlug,
      groups: modelSelectorGroups,
      onSelectModel: handleSelectModel,
    },
    advancedSettings: {
      t,
      temperature: [temperature],
      topP: [topP],
      defaultTemperature: DEFAULT_TEMPERATURE,
      defaultTopP: DEFAULT_TOP_P,
      onTemperatureChange: handleTemperatureChange,
      onTopPChange: handleTopPChange,
    },
  };
};
