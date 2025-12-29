import { useCallback } from "react";
import type { useChat } from "@ai-sdk/react";
import type { UIDataTypes, UIMessage, UITools } from "ai";
import type { ChatMessageMetadata } from "@/features/chat/types/chat";
import {
  buildRetryBody,
  resolveRetryContext,
} from "@/features/chat/hooks/chat-view-model-helpers";

type UseChatRetryArgs = {
  activeConversationId: string;
  messagesRef: React.RefObject<UIMessage<unknown, UIDataTypes, UITools>[]>;
  regenerate: ReturnType<typeof useChat>["regenerate"];
  defaultWebSearchEngine: string;
  useWebSearch: boolean;
};

export const useChatRetry = ({
  activeConversationId,
  messagesRef,
  regenerate,
  defaultWebSearchEngine,
  useWebSearch,
}: UseChatRetryArgs) => {
  const handleRetryMessage = useCallback(
    (messageId: string) => {
      const retryContext = resolveRetryContext(
        messagesRef.current as UIMessage<ChatMessageMetadata>[],
        messageId,
      );
      if (!retryContext) {
        // Only allow retry for assistant replies with a known parent user message.
        return;
      }
      const webSearchEngine = defaultWebSearchEngine.trim();
      const webSearch = useWebSearch
        ? {
            enabled: true,
            ...(webSearchEngine ? { engine: webSearchEngine } : {}),
          }
        : undefined;
      const body = buildRetryBody({
        activeConversationId,
        webSearch,
        parentMessageId: retryContext.parentMessageId,
      });
      void regenerate({ messageId, body });
    },
    [
      activeConversationId,
      defaultWebSearchEngine,
      messagesRef,
      regenerate,
      useWebSearch,
    ],
  );

  return {
    handleRetryMessage,
  };
};
