import { useCallback, useMemo, useState } from "react";
import { updateMessageReaction } from "@/services/api/messages";
import type { UIMessage } from "ai";
import type { ChatMessageMetadata } from "@/features/chat/types/chat";

type UseChatMessageReactionsArgs = {
  activeConversationId: string;
  messages: UIMessage<ChatMessageMetadata>[];
};

export const useChatMessageReactions = ({
  activeConversationId,
  messages,
}: UseChatMessageReactionsArgs) => {
  const [reactionOverrides, setReactionOverrides] = useState<
    Record<string, "like" | "dislike" | null>
  >({});

  const reactionById = useMemo(() => {
    const next: Record<string, "like" | "dislike" | null> = {};
    const knownIds = new Set(messages.map((message) => message.id));
    for (const message of messages) {
      next[message.id] = message.metadata?.reaction ?? null;
    }
    for (const [messageId, reaction] of Object.entries(reactionOverrides)) {
      if (knownIds.has(messageId)) {
        next[messageId] = reaction;
      }
    }
    return next;
  }, [messages, reactionOverrides]);

  const handleToggleReaction = useCallback(
    async (messageId: string, reaction: "like" | "dislike") => {
      const previous = reactionById[messageId] ?? null;
      const nextReaction = previous === reaction ? null : reaction;
      setReactionOverrides((prev) => ({ ...prev, [messageId]: nextReaction }));
      if (!activeConversationId) {
        return;
      }
      const result = await updateMessageReaction(
        activeConversationId,
        messageId,
        nextReaction,
      );
      if (!result) {
        // Revert on failure so the UI does not drift from the server state.
        setReactionOverrides((prev) => ({ ...prev, [messageId]: previous }));
      }
    },
    [activeConversationId, reactionById],
  );

  return {
    reactionById,
    handleToggleReaction,
  };
};
