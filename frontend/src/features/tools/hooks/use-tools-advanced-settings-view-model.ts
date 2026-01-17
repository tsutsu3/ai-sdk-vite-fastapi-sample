import { useCallback, useState } from "react";
import type { ToolsAdvancedSettingsViewModel } from "@/features/tools/hooks/tools-view-model-types";

type UseToolsAdvancedSettingsViewModelArgs = {
  t: (key: string, params?: Record<string, unknown>) => string;
};

export const useToolsAdvancedSettingsViewModel = ({
  t,
}: UseToolsAdvancedSettingsViewModelArgs): ToolsAdvancedSettingsViewModel => {
  const defaultTemperature = 1;
  const defaultTopP = 1;
  const defaultHydeEnabled = false;
  const defaultMaxDocuments = 5;
  const defaultInjectedPrompt = "";
  const [temperature, setTemperature] = useState(defaultTemperature);
  const [topP, setTopP] = useState(defaultTopP);
  const [hydeEnabled, setHydeEnabled] = useState(defaultHydeEnabled);
  const [maxDocuments, setMaxDocuments] = useState(defaultMaxDocuments);
  const [injectedPrompt, setInjectedPrompt] = useState(defaultInjectedPrompt);

  const handleTemperatureChange = useCallback((value: number[]) => {
    setTemperature(value[0] ?? defaultTemperature);
  }, [defaultTemperature]);

  const handleTopPChange = useCallback((value: number[]) => {
    setTopP(value[0] ?? defaultTopP);
  }, [defaultTopP]);

  const handleHydeToggle = useCallback(() => {
    setHydeEnabled((prev) => !prev);
  }, []);

  const handleMaxDocumentsChange = useCallback((value: number[]) => {
    setMaxDocuments(value[0] ?? defaultMaxDocuments);
  }, [defaultMaxDocuments]);

  const handleInjectedPromptChange = useCallback((value: string) => {
    setInjectedPrompt(value);
  }, []);

  return {
    t,
    temperature: [temperature],
    topP: [topP],
    hydeEnabled,
    maxDocuments: [maxDocuments],
    injectedPrompt,
    defaultTemperature,
    defaultTopP,
    defaultHydeEnabled,
    defaultMaxDocuments,
    onTemperatureChange: handleTemperatureChange,
    onTopPChange: handleTopPChange,
    onHydeToggle: handleHydeToggle,
    onMaxDocumentsChange: handleMaxDocumentsChange,
    onInjectedPromptChange: handleInjectedPromptChange,
  };
};
