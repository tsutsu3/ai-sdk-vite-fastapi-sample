import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import type {
  ChatMessageListViewModel,
  ChatScrollViewModel,
} from "@/features/chat/hooks/chat-view-model-types";
import type { ChatStatus } from "ai";

export type ToolsAdvancedSettingsViewModel = {
  t: (key: string, params?: Record<string, unknown>) => string;
  temperature: number[];
  topP: number[];
  hydeEnabled: boolean;
  maxDocuments: number[];
  defaultTemperature: number;
  defaultTopP: number;
  defaultHydeEnabled: boolean;
  defaultMaxDocuments: number;
  onTemperatureChange: (value: number[]) => void;
  onTopPChange: (value: number[]) => void;
  onHydeToggle: () => void;
  onMaxDocumentsChange: (value: number[]) => void;
};

export type ToolsPromptInputViewModel = {
  t: (key: string) => string;
  text: string;
  status: ChatStatus;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  onSubmitPrompt: (message: PromptInputMessage) => void;
  onTextChange: (value: string) => void;
  onTranscriptionChange: (value: string) => void;
  advancedSettings: ToolsAdvancedSettingsViewModel;
};

export type ToolsChainOfThoughtStep = {
  id: string;
  label: string;
  description?: string;
  status?: "complete" | "active" | "pending";
};

export type ToolsChainOfThoughtViewModel = {
  steps: ToolsChainOfThoughtStep[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export type ToolsSourceItem = {
  id: string;
  title: string;
  url?: string;
  description?: string;
};

export type ToolsSourcesViewModel = {
  items: ToolsSourceItem[];
};

export type ToolsEmptyStateViewModel = {
  eyebrow: string;
  title: string;
  subtitle: string;
  samples: string[];
};

export type ToolsViewModel = {
  status: ChatStatus;
  scroll: ChatScrollViewModel;
  messageList: ChatMessageListViewModel;
  prompt: ToolsPromptInputViewModel;
  emptyState: ToolsEmptyStateViewModel;
  chainOfThought: ToolsChainOfThoughtViewModel;
  sources: ToolsSourcesViewModel;
};
