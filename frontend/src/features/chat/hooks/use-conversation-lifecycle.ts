import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { useAppStore } from "@/store/app-store";
import { useStateWithRef } from "@/features/chat/hooks/use-state-with-ref";
import {
  isConversationDataEvent,
  isTitleDataEvent,
  type RawDataEvent,
} from "@/features/chat/hooks/chat-view-model-helpers";

type UseConversationLifecycleArgs = {
  scope: "chat" | "tools";
  toolId?: string;
  onConversationChanged?: (conversationId: string) => void;
};

export const useConversationLifecycle = ({
  scope,
  toolId,
  onConversationChanged,
}: UseConversationLifecycleArgs) => {
  const { id: conversationId } = useParams();
  const navigate = useNavigate();
  const upsertHistoryItem = useAppStore((state) => state.upsertHistoryItem);
  const [localConversationId, setLocalConversationId] = useState<string | null>(
    null,
  );
  const skipMessageFetchForIdRef = useRef<string | null>(null);

  const {
    state: activeConversationId,
    ref: activeConversationRef,
    setState: setActiveConversationId,
  } = useStateWithRef<string>(conversationId ?? localConversationId ?? "");

  const resetConversation = useCallback(() => {
    skipMessageFetchForIdRef.current = null;
    setLocalConversationId(null);
    setActiveConversationId("");
  }, [setActiveConversationId]);

  useEffect(() => {
    const nextId = conversationId ?? localConversationId ?? "";
    if (activeConversationRef.current === nextId) {
      // Skip state updates to avoid navigation loops and redundant renders.
      return;
    }
    setActiveConversationId(nextId);
  }, [
    conversationId,
    localConversationId,
    setActiveConversationId,
    activeConversationRef,
  ]);

  const resolveHistoryUrl = useCallback(
    (nextConversationId: string) => {
      if (scope === "tools") {
        return toolId
          ? `/tools/${toolId}/c/${nextConversationId}`
          : `/tools/c/${nextConversationId}`;
      }
      return `/chat/c/${nextConversationId}`;
    },
    [scope, toolId]
  );


  const handleDataEvent = (data: RawDataEvent) => {
    if (isConversationDataEvent(data)) {
      const nextConversationId = data.data.convId.trim();
      if (!nextConversationId) {
        // Ignore empty ids from partial streaming payloads.
        return;
      }
      if (conversationId && conversationId === nextConversationId) {
        setActiveConversationId(nextConversationId);
        return;
      }
      if (activeConversationRef.current === nextConversationId) {
        // Prevent re-processing the same conversation id.
        return;
      }
      setActiveConversationId(nextConversationId);
      skipMessageFetchForIdRef.current = nextConversationId;
      setLocalConversationId(nextConversationId);
      onConversationChanged?.(nextConversationId);
      if (!conversationId) {
        navigate(resolveHistoryUrl(nextConversationId));
      }
      upsertHistoryItem({
        name: scope === "tools" ? "New Tool Chat" : "New Chat",
        url: resolveHistoryUrl(nextConversationId),
        updatedAt: new Date().toISOString(),
      });
      return;
    }

    if (!isTitleDataEvent(data)) return;

    const conversationIdForEvent = activeConversationRef.current;
    if (!conversationIdForEvent) return;

    const titleValue = data.data.title.trim();
    if (!titleValue) return;

    upsertHistoryItem({
      name: titleValue,
      url: resolveHistoryUrl(conversationIdForEvent),
      updatedAt: new Date().toISOString(),
    });
  };

  return {
    activeConversationId,
    activeConversationRef,
    setActiveConversationId,
    skipMessageFetchForIdRef,
    handleDataEvent,
    resetConversation,
  };
};
