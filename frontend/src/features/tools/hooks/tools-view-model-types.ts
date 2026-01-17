import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import type {
  ChatMessageListViewModel,
  ChatScrollViewModel,
} from "@/features/chat/hooks/chat-view-model-types";
import type { RagProgressStep } from "@/shared/types/rag-progress";
import type { RagSourceItem } from "@/shared/types/rag-sources";
import type { ChatStatus } from "ai";

export type ToolsAdvancedSettingsViewModel = {
  t: (key: string, params?: Record<string, unknown>) => string;
  temperature: number[];
  topP: number[];
  hydeEnabled: boolean;
  maxDocuments: number[];
  injectedPrompt: string;
  defaultTemperature: number;
  defaultTopP: number;
  defaultHydeEnabled: boolean;
  defaultMaxDocuments: number;
  onTemperatureChange: (value: number[]) => void;
  onTopPChange: (value: number[]) => void;
  onHydeToggle: () => void;
  onMaxDocumentsChange: (value: number[]) => void;
  onInjectedPromptChange: (value: string) => void;
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

export type ToolsChainOfThoughtStep = RagProgressStep;

export type ToolsSourceItem = RagSourceItem;


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
};
