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
};

export const useChatRetry = ({
  activeConversationId,
  messagesRef,
  regenerate,
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
      const body = buildRetryBody({
        activeConversationId,
        parentMessageId: retryContext.parentMessageId,
      });
      void regenerate({ messageId, body });
    },
    [
      activeConversationId,
      messagesRef,
      regenerate,
    ],
  );

  return {
    handleRetryMessage,
  };
};
