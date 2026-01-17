import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import type { ChatModel, ChatMessageMetadata } from "@/features/chat/types/chat";
import type { RagProgressStep } from "@/shared/types/rag-progress";
import type { RagSourceItem } from "@/shared/types/rag-sources";
import type { ChatStatus, UIMessage } from "ai";
import type { StickToBottomContext } from "use-stick-to-bottom";

export type ChatModelSelectorViewModel = {
  t: (key: string) => string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedModelId: string;
  selectedModelName?: string;
  selectedModelChefSlug?: string;
  groups: Array<{ chef: string; models: ChatModel[] }>;
  onSelectModel: (modelId: string) => void;
};

export type ChatAdvancedSettingsViewModel = {
  t: (key: string, params?: Record<string, unknown>) => string;
  temperature: number[];
  topP: number[];
  defaultTemperature: number;
  defaultTopP: number;
  onTemperatureChange: (value: number[]) => void;
  onTopPChange: (value: number[]) => void;
};

export type ChatPromptInputViewModel = {
  t: (key: string) => string;
  text: string;
  status: ChatStatus;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  onSubmitPrompt: (message: PromptInputMessage) => void;
  onTextChange: (value: string) => void;
  onTranscriptionChange: (value: string) => void;
  modelSelector: ChatModelSelectorViewModel;
  advancedSettings: ChatAdvancedSettingsViewModel;
};

export type ChatMessageListViewModel = {
  messages: UIMessage<ChatMessageMetadata>[];
  models: ChatModel[];
  reactionById: Record<string, "like" | "dislike" | null>;
  onToggleReaction: (messageId: string, reaction: "like" | "dislike") => void;
  onRetryMessage: (messageId: string) => void;
  t: (key: string) => string;
  copiedMessageId: string | null;
  onCopyMessage: (message: UIMessage<ChatMessageMetadata>) => void;
  getModelIdForMessage: (messageIndex: number) => string | undefined;
  ragProgressByMessageId?: Record<string, RagProgressStep[]>;
  ragSourcesByMessageId?: Record<string, RagSourceItem[]>;
};

export type ChatScrollViewModel = {
  setScrollContextRef: React.RefCallback<StickToBottomContext>;
  setTopSentinelRef: React.RefCallback<HTMLDivElement>;
};

export type ChatViewModel = {
  status: ChatStatus;
  scroll: ChatScrollViewModel;
  messageList: ChatMessageListViewModel;
  prompt: ChatPromptInputViewModel;
};
