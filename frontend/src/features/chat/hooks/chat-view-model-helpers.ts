import type { ChatMessageMetadata } from "@/features/chat/types/chat";
import type { UIDataTypes, UIMessage, UITools } from "ai";

export type RawDataEvent = {
  type: `data-${string}`;
  id?: string;
  data: unknown;
};

export type DataEventMap = {
  "data-title": {
    title: string;
  };
  "data-conversation": {
    convId: string;
    messageId?: string;
  };
  "data-model": {
    messageId: string;
    modelId: string;
  };
};

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function isTitleDataEvent(
  event: RawDataEvent,
): event is { type: "data-title"; data: DataEventMap["data-title"] } {
  return (
    event.type === "data-title" &&
    isRecord(event.data) &&
    typeof event.data.title === "string"
  );
}

export function isConversationDataEvent(
  event: RawDataEvent,
): event is {
  type: "data-conversation";
  data: DataEventMap["data-conversation"];
} {
  return (
    event.type === "data-conversation" &&
    isRecord(event.data) &&
    typeof event.data.convId === "string"
  );
}

export function isModelDataEvent(
  event: RawDataEvent,
): event is { type: "data-model"; data: DataEventMap["data-model"] } {
  return (
    event.type === "data-model" &&
    isRecord(event.data) &&
    typeof event.data.messageId === "string" &&
    typeof event.data.modelId === "string"
  );
}

/**
 * Normalizes chat messages to ensure typed metadata.
 *
 * `useChat` provides `metadata` as `unknown`, so this narrows it to
 * `ChatMessageMetadata` when possible, or `undefined` otherwise,
 * allowing safe access in the UI.
 */
export function normalizeChatMessages(
  messages: UIMessage<unknown, UIDataTypes, UITools>[],
): UIMessage<ChatMessageMetadata, UIDataTypes, UITools>[] {
  return messages.map((message) => ({
    ...message,
    metadata: isRecord(message.metadata)
      ? (message.metadata as ChatMessageMetadata)
      : undefined,
  }));
}

export function resolveErrorText(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  if (isRecord(error) && typeof error.errorText === "string") {
    return error.errorText;
  }
  return "Unexpected error while generating a response.";
}

export type RetryContext = {
  messageId: string;
  parentMessageId: string;
};

export function resolveRetryContext(
  messages: UIMessage<ChatMessageMetadata>[],
  messageId: string,
): RetryContext | null {
  const messageIndex = messages.findIndex((message) => message.id === messageId);
  if (messageIndex < 0) {
    return null;
  }
  const targetMessage = messages[messageIndex];
  if (targetMessage?.role !== "assistant") {
    return null;
  }
  for (let i = messageIndex - 1; i >= 0; i -= 1) {
    if (messages[i]?.role === "user") {
      return { messageId, parentMessageId: messages[i].id };
    }
  }
  return null;
}

export function buildRetryBody({
  activeConversationId,
  webSearch,
  parentMessageId,
}: {
  activeConversationId: string;
  webSearch?: { enabled: boolean; engine?: string };
  parentMessageId?: string;
}) {
  return {
    ...(webSearch ? { webSearch } : {}),
    ...(activeConversationId ? { chatId: activeConversationId } : {}),
    ...(parentMessageId ? { parentMessageId } : {}),
  };
}
