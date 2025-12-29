import { useCallback, useMemo, useState } from "react";
import type { UIDataTypes, UIMessage, UITools } from "ai";
import { normalizeChatMessages } from "@/features/chat/hooks/chat-view-model-helpers";
import type { ChatMessageMetadata } from "@/features/chat/types/chat";

type ModelDataEvent = {
  data: {
    messageId: string;
    modelId: string;
  };
};

type UseChatModelMetadataArgs = {
  messages: UIMessage<unknown, UIDataTypes, UITools>[];
};

export const useChatModelMetadata = ({
  messages,
}: UseChatModelMetadataArgs) => {
  const [modelIdByMessageId, setModelIdByMessageId] = useState<
    Record<string, string>
  >({});

  const applyModelDataEvent = useCallback((event: ModelDataEvent) => {
    setModelIdByMessageId((prev) => ({
      ...prev,
      [event.data.messageId]: event.data.modelId,
    }));
  }, []);

  const normalizedMessages = useMemo(() => {
    const base = normalizeChatMessages(messages);
    return base.map((message) => {
      if (message.metadata?.modelId) {
        return message;
      }
      const modelId = modelIdByMessageId[message.id];
      if (!modelId) {
        return message;
      }
      return {
        ...message,
        metadata: {
          ...(message.metadata ?? {}),
          modelId,
        },
      } as UIMessage<ChatMessageMetadata>;
    });
  }, [messages, modelIdByMessageId]);

  return {
    normalizedMessages,
    applyModelDataEvent,
  };
};
