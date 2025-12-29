import { useCallback, useEffect, useState } from "react";
import type { UIMessage } from "ai";
import type { ChatMessageMetadata } from "@/features/chat/types/chat";

type UseChatMessageListViewModelArgs = {
  messages: UIMessage<ChatMessageMetadata>[];
};

export const useChatMessageListViewModel = ({
  messages,
}: UseChatMessageListViewModelArgs) => {
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  const getModelIdForMessage = useCallback(
    (messageIndex: number): string | undefined =>
      messages[messageIndex]?.metadata?.modelId,
    [messages],
  );

  const resolveMessageText = useCallback(
    (message: UIMessage<ChatMessageMetadata>) =>
      message.parts
        .filter((part) => part.type === "text")
        .map((part) => (typeof part.text === "string" ? part.text : ""))
        .join("\n")
        .trim(),
    [],
  );

  const handleCopy = useCallback(
    async (message: UIMessage<ChatMessageMetadata>) => {
      const text = resolveMessageText(message);
      if (!text) {
        return;
      }

      try {
        await navigator.clipboard.writeText(text);
      } catch {
        return;
      }

      setCopiedMessageId(message.id);
    },
    [resolveMessageText],
  );

  useEffect(() => {
    if (!copiedMessageId) {
      return;
    }

    const timer = setTimeout(() => {
      setCopiedMessageId(null);
    }, 3000);

    return () => {
      clearTimeout(timer);
    };
  }, [copiedMessageId]);

  return {
    copiedMessageId,
    handleCopy,
    getModelIdForMessage,
  };
};
