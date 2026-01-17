import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import type { ChatStatus, UIMessage } from "ai";
import type { ChatMessageMetadata } from "@/features/chat/types/chat";
import { useAppStore } from "@/store/app-store";
import { fetchConversationMessages } from "@/services/api/conversations";
import { updateMessageReaction } from "@/services/api/messages";
import { useTranslation } from "react-i18next";
import type { StickToBottomContext } from "use-stick-to-bottom";
import { useChatMessageListViewModel } from "@/features/chat/hooks/use-chat-message-list-view-model";
import {
  isConversationDataEvent,
  isTitleDataEvent,
  isModelDataEvent,
  normalizeChatMessages,
  resolveErrorText,
} from "@/features/chat/hooks/chat-view-model-helpers";
import { useChatModelSettingsViewModel } from "@/features/chat/hooks/use-chat-model-settings-view-model";
import { useToolsAdvancedSettingsViewModel } from "@/features/tools/hooks/use-tools-advanced-settings-view-model";
import { useToolsInputViewModel } from "@/features/tools/hooks/use-tools-input-view-model";
import type {
  ToolsChainOfThoughtStep,
  ToolsSourceItem,
  ToolsViewModel,
} from "@/features/tools/hooks/tools-view-model-types";
import {
  buildToolsRequestBody,
  isChainOfThoughtDataEvent,
  isSourcesDataEvent,
  mergeChainOfThoughtSteps,
  mergeSources,
} from "@/features/tools/hooks/tools-view-model-helpers";

export const useToolsViewModel = (): ToolsViewModel => {
  const [loadingOlderMessages, setLoadingOlderMessages] =
    useState<boolean>(false);
  const [messagesContinuationToken, setMessagesContinuationToken] = useState<
    string | null
  >(null);
  const [reactionById, setReactionById] = useState<
    Record<string, "like" | "dislike" | null>
  >({});
  const [ragProgressByMessageId, setRagProgressByMessageId] = useState<
    Record<string, ToolsChainOfThoughtStep[]>
  >({});
  const [ragSourcesByMessageId, setRagSourcesByMessageId] = useState<
    Record<string, ToolsSourceItem[]>
  >({});
  const [modelIdByMessageId, setModelIdByMessageId] = useState<
    Record<string, string>
  >({});
  const scrollContextRef = useRef<StickToBottomContext | null>(null);
  const topSentinelRef = useRef<HTMLDivElement | null>(null);
  const setScrollContextRef = useCallback((value: StickToBottomContext | null) => {
    scrollContextRef.current = value;
  }, []);
  const setTopSentinelRef = useCallback((value: HTMLDivElement | null) => {
    topSentinelRef.current = value;
  }, []);
  const { id: conversationId, type: toolId } = useParams();
  const navigate = useNavigate();
  const upsertHistoryItem = useAppStore((state) => state.upsertHistoryItem);
  const capabilities = useAppStore((state) => state.capabilities);
  const { t } = useTranslation();
  const [localConversationId, setLocalConversationId] = useState<string | null>(
    null,
  );
  const messagePageSize = Math.max(
    capabilities.apiPageSizes.messagesPageSizeDefault || 30,
    1,
  );
  const skipMessageFetchForIdRef = useRef<string | null>(null);
  const activeConversationId = conversationId ?? localConversationId ?? "";
  const activeConversationIdRef = useRef<string>("");
  const activeRagMessageIdRef = useRef<string>("");
  const toolIdRef = useRef<string>("");
  const messagesRef = useRef<UIMessage[]>([]);
  const statusRef = useRef<ChatStatus>("ready");
  const messagesConversationIdRef = useRef<string>("");
  const modelSettings = useChatModelSettingsViewModel({ t });
  const advancedSettings = useToolsAdvancedSettingsViewModel({ t });

  const { messages, status, sendMessage, regenerate, setMessages, stop } =
    useChat({
      transport: new DefaultChatTransport({
        api: "/api/rag/query",
        prepareSendMessagesRequest: ({ messages, body }) => ({
          body: {
            ...buildToolsRequestBody({
              toolId: typeof body?.toolId === "string" ? body.toolId : "",
              maxDocuments:
                typeof body?.maxDocuments === "number" ? body.maxDocuments : undefined,
              injectedPrompt:
                typeof body?.injectedPrompt === "string"
                  ? body.injectedPrompt
                  : undefined,
              hydeEnabled:
                typeof body?.hydeEnabled === "boolean"
                  ? body.hydeEnabled
                  : undefined,
              chatId:
                typeof body?.chatId === "string"
                  ? body.chatId
                  : activeConversationId || undefined,
              messages,
            }),
          },
        }),
      }),
      onError: (error) => {
        console.error("Tools chat error:", error);
        const errorText = resolveErrorText(error);
        const errorMessage: UIMessage = {
          id: `err-${crypto.randomUUID()}`,
          role: "assistant",
          parts: [{ type: "text", text: `Error: ${errorText}` }],
          metadata: { isError: true },
        };
        setMessages((prev) => [...prev, errorMessage]);
      },
      onData: (data) => {
        if (isConversationDataEvent(data)) {
          const nextConversationId = data.data.convId.trim();
          if (!nextConversationId) {
            return;
          }
          const toolIdFromEvent =
            typeof data.data.toolId === "string" ? data.data.toolId.trim() : "";
          const resolvedToolId = toolIdFromEvent || toolId || "";
          if (conversationId && conversationId === nextConversationId) {
            activeConversationIdRef.current = nextConversationId;
            toolIdRef.current = resolvedToolId;
            return;
          }
          if (activeConversationIdRef.current === nextConversationId) {
            return;
          }
          activeConversationIdRef.current = nextConversationId;
          toolIdRef.current = resolvedToolId;
          skipMessageFetchForIdRef.current = nextConversationId;
          messagesConversationIdRef.current = nextConversationId;
          setLocalConversationId(nextConversationId);
          if (!conversationId) {
            const toolPath = resolvedToolId
              ? `/tools/${resolvedToolId}/c/${nextConversationId}`
              : `/tools/c/${nextConversationId}`;
            navigate(toolPath);
          }
          const historyUrl = resolvedToolId
            ? `/tools/${resolvedToolId}/c/${nextConversationId}`
            : `/tools/c/${nextConversationId}`;
          upsertHistoryItem({
            name: "New Tool Chat",
            url: historyUrl,
            updatedAt: new Date().toISOString(),
          });
          return;
        }

        if (isModelDataEvent(data)) {
          setModelIdByMessageId((prev) => ({
            ...prev,
            [data.data.messageId]: data.data.modelId,
          }));
          activeRagMessageIdRef.current = data.data.messageId;
          return;
        }

        if (isChainOfThoughtDataEvent(data)) {
          const ragMessageId = activeRagMessageIdRef.current;
          if (!ragMessageId) {
            return;
          }
          setRagProgressByMessageId((prev) => ({
            ...prev,
            [ragMessageId]: mergeChainOfThoughtSteps(
              prev[ragMessageId] ?? [],
              data.data,
            ),
          }));
          return;
        }

        if (isSourcesDataEvent(data)) {
          const ragMessageId = activeRagMessageIdRef.current;
          if (!ragMessageId) {
            return;
          }
          setRagSourcesByMessageId((prev) => ({
            ...prev,
            [ragMessageId]: mergeSources(prev[ragMessageId] ?? [], data.data),
          }));
          return;
        }

        if (!isTitleDataEvent(data)) return;

        const conversationIdForEvent = activeConversationIdRef.current;
        if (!conversationIdForEvent) return;

        const titleValue = data.data.title.trim();
        if (!titleValue) return;

        const resolvedToolId = toolIdRef.current || toolId || "";
        const historyUrl = resolvedToolId
          ? `/tools/${resolvedToolId}/c/${conversationIdForEvent}`
          : `/tools/c/${conversationIdForEvent}`;
        upsertHistoryItem({
          name: titleValue,
          url: historyUrl,
          updatedAt: new Date().toISOString(),
        });
      },
    });

  useEffect(() => {
    activeConversationIdRef.current = activeConversationId;
  }, [activeConversationId]);

  useEffect(() => {
    if (!activeConversationId) {
      setRagProgressByMessageId({});
      setRagSourcesByMessageId({});
      activeRagMessageIdRef.current = "";
      toolIdRef.current = "";
    }
  }, [activeConversationId]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    let mounted = true;
    if (!activeConversationId) {
      setMessages([]);
      setMessagesContinuationToken(null);
      messagesConversationIdRef.current = "";
      return () => {
        mounted = false;
      };
    }
    if (skipMessageFetchForIdRef.current === activeConversationId) {
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
            return;
          }
          if (ordered.length < currentMessages.length) {
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
  }, [activeConversationId, messagePageSize, setMessages]);

  useEffect(() => {
    if (!conversationId) {
      setLocalConversationId(null);
    }
  }, [conversationId]);

  const handleLoadOlderMessages = useCallback(async () => {
    if (
      !activeConversationId ||
      loadingOlderMessages ||
      !messagesContinuationToken
    ) {
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
      if (activeConversationIdRef.current !== conversationIdAtCall) {
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
    loadingOlderMessages,
    messagePageSize,
    messagesContinuationToken,
    setMessages,
  ]);

  const handleRetryMessage = useCallback(
    (messageId: string) => {
      const currentMessages =
        messagesRef.current as UIMessage<ChatMessageMetadata>[];
      const messageIndex = currentMessages.findIndex(
        (message) => message.id === messageId,
      );
      if (messageIndex < 0) {
        return;
      }
      const targetMessage = currentMessages[messageIndex];
      if (targetMessage?.role !== "assistant") {
        return;
      }
      let userMessage: UIMessage<ChatMessageMetadata> | null = null;
      for (let i = messageIndex - 1; i >= 0; i -= 1) {
        if (currentMessages[i]?.role === "user") {
          userMessage = currentMessages[i] as UIMessage<ChatMessageMetadata>;
          break;
        }
      }
      if (!userMessage) {
        return;
      }
      const body = {
        toolId: toolId ?? "",
        maxDocuments: advancedSettings.maxDocuments[0],
        injectedPrompt: advancedSettings.injectedPrompt,
        hydeEnabled: advancedSettings.hydeEnabled,
        ...(activeConversationId ? { chatId: activeConversationId } : {}),
      };
      void regenerate({ messageId, body });
    },
    [
      advancedSettings.maxDocuments,
      activeConversationId,
      regenerate,
      toolId,
    ],
  );

  const handleToggleReaction = useCallback(
    async (messageId: string, reaction: "like" | "dislike") => {
      const previous = reactionById[messageId] ?? null;
      const nextReaction = previous === reaction ? null : reaction;
      setReactionById((prev) => ({ ...prev, [messageId]: nextReaction }));
      if (!activeConversationId) {
        return;
      }
      const result = await updateMessageReaction(
        activeConversationId,
        messageId,
        nextReaction,
      );
      if (!result) {
        setReactionById((prev) => ({ ...prev, [messageId]: previous }));
      }
    },
    [activeConversationId, reactionById],
  );

  const hasMoreMessages = Boolean(messagesContinuationToken);
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
      };
    });
  }, [messages, modelIdByMessageId]);

  useEffect(() => {
    setReactionById((prev) => {
      const next = { ...prev };
      const knownIds = new Set(
        normalizedMessages.map((message) => message.id),
      );
      for (const message of normalizedMessages) {
        if (message.metadata?.reaction) {
          next[message.id] = message.metadata.reaction;
        } else if (!(message.id in next)) {
          next[message.id] = null;
        }
      }
      for (const key of Object.keys(next)) {
        if (!knownIds.has(key)) {
          delete next[key];
        }
      }
      return next;
    });
  }, [normalizedMessages]);

  const messageList = useChatMessageListViewModel({
    messages: normalizedMessages,
  });

  const handleLoadMore = useCallback(async () => {
    if (!hasMoreMessages || loadingOlderMessages) {
      return;
    }
    const scrollElement = scrollContextRef.current?.scrollRef.current;
    const previousScrollHeight = scrollElement?.scrollHeight ?? 0;
    const previousScrollTop = scrollElement?.scrollTop ?? 0;
    const added = await handleLoadOlderMessages();
    if (!added || !scrollElement) {
      return;
    }
    requestAnimationFrame(() => {
      const nextScrollHeight = scrollElement.scrollHeight;
      scrollElement.scrollTop =
        previousScrollTop + (nextScrollHeight - previousScrollHeight);
    });
  }, [handleLoadOlderMessages, hasMoreMessages, loadingOlderMessages]);

  useEffect(() => {
    const scrollElement = scrollContextRef.current?.scrollRef.current;
    const sentinel = topSentinelRef.current;
    if (!scrollElement || !sentinel) {
      return;
    }
    if (!hasMoreMessages) {
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          handleLoadMore();
        }
      },
      {
        root: scrollElement,
        rootMargin: "200px 0px 0px 0px",
        threshold: 0,
      },
    );
    observer.observe(sentinel);
    return () => {
      observer.disconnect();
    };
  }, [handleLoadMore, hasMoreMessages]);

  const prompt = useToolsInputViewModel({
    t,
    status,
    sendMessage,
    stop,
    toolId: toolId ?? "",
    activeConversationId,
    advancedSettings,
  });

  const toolKey = toolId ?? "default";
  const toolLabelKey = toolId ? `tool${toolId.replace(/^rag/i, "")}` : "";
  const toolLabel = toolLabelKey
    ? t(toolLabelKey, { defaultValue: toolId })
    : t("toolsEmptyFallbackToolLabel");
  const toolContent = t(`toolsEmptyContent.${toolKey}`, {
    returnObjects: true,
  });
  const defaultContent = t("toolsEmptyContent.default", {
    returnObjects: true,
  });
  const resolvedContent =
    toolContent && typeof toolContent === "object" ? toolContent : defaultContent;
  const samples = Array.isArray(resolvedContent?.samples)
    ? resolvedContent.samples
    : [];

  return {
    status,
    scroll: {
      setScrollContextRef,
      setTopSentinelRef,
    },
    messageList: {
      messages: normalizedMessages,
      models: modelSettings.models,
      reactionById,
      onToggleReaction: handleToggleReaction,
      onRetryMessage: handleRetryMessage,
      t,
      copiedMessageId: messageList.copiedMessageId,
      onCopyMessage: messageList.handleCopy,
      getModelIdForMessage: messageList.getModelIdForMessage,
      ragProgressByMessageId,
      ragSourcesByMessageId,
    },
    prompt,
    emptyState: {
      eyebrow: t("toolsEmptyEyebrow", { tool: toolLabel }),
      title:
        typeof resolvedContent?.title === "string"
          ? resolvedContent.title
          : t("toolsEmptyTitle", { tool: toolLabel }),
      subtitle:
        typeof resolvedContent?.subtitle === "string"
          ? resolvedContent.subtitle
          : t("toolsEmptySubtitle", { tool: toolLabel }),
      samples: samples.slice(0, 3),
    },
  };
};
