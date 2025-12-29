import { useCallback, useEffect, useRef, useState } from "react";
import type { UIMessage } from "ai";
import { fetchConversationMessages } from "@/services/api/conversations";

type UseConversationMessagesArgs = {
  activeConversationId: string;
  activeConversationRef: React.RefObject<string>;
  skipMessageFetchForIdRef: React.RefObject<string | null>;
  messagePageSize: number;
  messages: UIMessage[];
  status: "ready" | "submitted" | "streaming" | "error";
  setMessages: (messages: UIMessage[] | ((prev: UIMessage[]) => UIMessage[])) => void;
};

export const useConversationMessages = ({
  activeConversationId,
  activeConversationRef,
  skipMessageFetchForIdRef,
  messagePageSize,
  messages,
  status,
  setMessages,
}: UseConversationMessagesArgs) => {
  const [loadingOlderMessages, setLoadingOlderMessages] =
    useState<boolean>(false);
  const [messagesContinuationToken, setMessagesContinuationToken] = useState<
    string | null
  >(null);
  const messagesRef = useRef<UIMessage[]>([]);
  const statusRef = useRef<"ready" | "submitted" | "streaming" | "error">(
    "ready",
  );
  const messagesConversationIdRef = useRef<string>("");

  const setMessagesConversationId = useCallback((value: string) => {
    messagesConversationIdRef.current = value;
  }, []);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    let mounted = true;
    if (!activeConversationId) {
      // Clear state when leaving a conversation to avoid leaking old messages.
      setMessages([]);
      setMessagesContinuationToken(null);
      messagesConversationIdRef.current = "";
      return () => {
        mounted = false;
      };
    }
    if (skipMessageFetchForIdRef.current === activeConversationId) {
      // Skip the fetch when the id is fresh from streaming data to prevent flicker.
      skipMessageFetchForIdRef.current = null;
      setMessagesContinuationToken(null);
      messagesConversationIdRef.current = activeConversationId;
      return () => {
        mounted = false;
      };
    }
    const controller = new AbortController();
    fetchConversationMessages(activeConversationId, {
      limit: messagePageSize,
      continuationToken: null,
      signal: controller.signal,
    })
      .then(({ messages: nextMessages, continuationToken }) => {
        if (!mounted) {
          return;
        }
        const ordered = nextMessages.slice().reverse();
        const currentMessages = messagesRef.current;
        const currentStatus = statusRef.current;
        const isSameConversation =
          messagesConversationIdRef.current === activeConversationId;
        if (isSameConversation) {
          if (
            ordered.length === 0 &&
            currentMessages.length > 0 &&
            (currentStatus === "submitted" || currentStatus === "streaming")
          ) {
            // Avoid wiping optimistic messages while the assistant is responding.
            return;
          }
          if (ordered.length < currentMessages.length) {
            // Ignore partial history so we do not drop already loaded messages.
            return;
          }
        }
        setMessages(ordered);
        setMessagesContinuationToken(continuationToken);
        messagesConversationIdRef.current = activeConversationId;
      })
      .catch(() => {});
    return () => {
      mounted = false;
      controller.abort();
    };
  }, [activeConversationId, messagePageSize, setMessages, skipMessageFetchForIdRef]);

  const handleLoadOlderMessages = useCallback(async () => {
    if (
      !activeConversationId ||
      loadingOlderMessages ||
      !messagesContinuationToken
    ) {
      // Prevent overlapping fetches and stop when pagination is exhausted.
      return 0;
    }
    setLoadingOlderMessages(true);
    const conversationIdAtCall = activeConversationId;
    const tokenAtCall = messagesContinuationToken;
    try {
      const result = await fetchConversationMessages(conversationIdAtCall, {
        limit: messagePageSize,
        continuationToken: tokenAtCall,
      });
      if (activeConversationRef.current !== conversationIdAtCall) {
        return 0;
      }
      const ordered = result.messages.slice().reverse();
      if (!ordered.length) {
        setMessagesContinuationToken(result.continuationToken);
        return 0;
      }
      setMessages((prev) => {
        const existingIds = new Set(prev.map((item) => item.id));
        const next = ordered.filter((item) => !existingIds.has(item.id));
        return next.length ? [...next, ...prev] : prev;
      });
      setMessagesContinuationToken(result.continuationToken);
      return ordered.length;
    } catch {
      return 0;
    } finally {
      setLoadingOlderMessages(false);
    }
  }, [
    activeConversationId,
    activeConversationRef,
    loadingOlderMessages,
    messagePageSize,
    messagesContinuationToken,
    setMessages,
  ]);

  const hasMoreMessages = Boolean(messagesContinuationToken);

  return {
    messagesRef,
    statusRef,
    messagesConversationIdRef,
    setMessagesConversationId,
    loadingOlderMessages,
    hasMoreMessages,
    handleLoadOlderMessages,
  };
};
