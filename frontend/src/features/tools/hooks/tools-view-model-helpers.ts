import type { RawDataEvent } from "@/features/chat/hooks/chat-view-model-helpers";
import { isRecord } from "@/features/chat/hooks/chat-view-model-helpers";
import type {
  ToolsChainOfThoughtStep,
  ToolsSourceItem,
} from "@/features/tools/hooks/tools-view-model-types";
import type { UIMessage } from "ai";

export type ToolsChainOfThoughtEvent = {
  steps?: ToolsChainOfThoughtStep[];
  step?: ToolsChainOfThoughtStep;
  reset?: boolean;
  open?: boolean;
};

export type ToolsSourcesEvent = {
  sources?: ToolsSourceItem[];
  reset?: boolean;
};

export const isChainOfThoughtDataEvent = (
  event: RawDataEvent,
): event is { type: "data-cot"; data: ToolsChainOfThoughtEvent } => {
  return event.type === "data-cot" && isRecord(event.data);
};

export const isSourcesDataEvent = (
  event: RawDataEvent,
): event is { type: "data-sources"; data: ToolsSourcesEvent } => {
  return event.type === "data-sources" && isRecord(event.data);
};

export const mergeChainOfThoughtSteps = (
  current: ToolsChainOfThoughtStep[],
  incoming: ToolsChainOfThoughtEvent,
): ToolsChainOfThoughtStep[] => {
  if (Array.isArray(incoming.steps)) {
    return incoming.steps.filter(
      (step): step is ToolsChainOfThoughtStep =>
        isRecord(step) && typeof step.id === "string" && !!step.label,
    );
  }
  if (incoming.reset) {
    return [];
  }
  if (incoming.step && typeof incoming.step.id === "string") {
    const next = [...current];
    const index = next.findIndex((step) => step.id === incoming.step?.id);
    if (index >= 0) {
      next[index] = { ...next[index], ...incoming.step };
    } else {
      next.push(incoming.step);
    }
    return next;
  }
  return current;
};

export const mergeSources = (
  current: ToolsSourceItem[],
  incoming: ToolsSourcesEvent,
): ToolsSourceItem[] => {
  if (Array.isArray(incoming.sources)) {
    return incoming.sources.filter(
      (source): source is ToolsSourceItem =>
        isRecord(source) && typeof source.id === "string" && !!source.title,
    );
  }
  if (incoming.reset) {
    return [];
  }
  return current;
};

export const buildToolsRequestBody = ({
  toolId,
  messages,
  maxDocuments,
  chatId,
  injectedPrompt,
  hydeEnabled,
}: {
  toolId: string;
  messages: UIMessage[];
  maxDocuments?: number;
  chatId?: string;
  injectedPrompt?: string;
  hydeEnabled?: boolean;
}) => {
  const retrievalMessages = buildRetrievalMessages(messages);
  const query = findLastUserMessage(retrievalMessages);
  return {
    query,
    ...(chatId ? { chatId } : {}),
    ...(toolId ? { toolId } : {}),
    ...(typeof maxDocuments === "number" ? { topK: maxDocuments } : {}),
    ...(injectedPrompt ? { injectedPrompt } : {}),
    ...(typeof hydeEnabled === "boolean" ? { hydeEnabled } : {}),
    ...(retrievalMessages.length ? { messages: retrievalMessages } : {}),
  };
};

type RetrievalMessage = {
  role: "user" | "assistant" | "system";
  content: string;
};

const findLastUserMessage = (messages: RetrievalMessage[]): string => {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    if (messages[i].role === "user" && messages[i].content.trim()) {
      return messages[i].content.trim();
    }
  }
  return "";
};

const extractMessageText = (message: UIMessage): string => {
  const parts = Array.isArray(message.parts) ? message.parts : [];
  const textParts = parts
    .filter((part) => part?.type === "text" && typeof part.text === "string")
    .map((part) => part.text.trim())
    .filter(Boolean);
  if (textParts.length) {
    return textParts.join("\n");
  }
  return "";
};

const buildRetrievalMessages = (messages: UIMessage[]): RetrievalMessage[] => {
  return messages
    .map((message) => ({
      role: message.role as RetrievalMessage["role"],
      content: extractMessageText(message),
    }))
    .filter((message) => message.content.trim());
};
