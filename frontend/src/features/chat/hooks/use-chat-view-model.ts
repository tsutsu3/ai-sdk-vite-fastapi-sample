import { useEffect, useRef } from "react";
import { useChat } from "@ai-sdk/react";
import { useAppStore } from "@/store/app-store";
import { DefaultChatTransport } from "ai";
import type { UIMessage } from "ai";
import { useTranslation } from "react-i18next";
import { useChatMessageListViewModel } from "@/features/chat/hooks/use-chat-message-list-view-model";
import { useChatInputViewModel } from "@/features/chat/hooks/use-chat-input-view-model";
import { useChatModelSettingsViewModel } from "@/features/chat/hooks/use-chat-model-settings-view-model";
import { useConversationLifecycle } from "@/features/chat/hooks/use-conversation-lifecycle";
import { useConversationMessages } from "@/features/chat/hooks/use-conversation-messages";
import type {
  ChatViewModel,
} from "@/features/chat/hooks/chat-view-model-types";
import {
  isConversationDataEvent,
  isTitleDataEvent,
  isModelDataEvent,
  resolveErrorText,
} from "@/features/chat/hooks/chat-view-model-helpers";
import { useChatRouteReset } from "@/features/chat/hooks/use-chat-route-reset";
import { useChatScrollController } from "@/features/chat/hooks/use-chat-scroll-controller";
import { useChatMessageReactions } from "@/features/chat/hooks/use-chat-message-reactions";
import { useChatRetry } from "@/features/chat/hooks/use-chat-retry";
import { useChatModelMetadata } from "@/features/chat/hooks/use-chat-model-metadata";

export type {
  ChatAdvancedSettingsViewModel,
  ChatMessageListViewModel,
  ChatModelSelectorViewModel,
  ChatPromptInputViewModel,
  ChatScrollViewModel,
  ChatViewModel,
} from "@/features/chat/hooks/chat-view-model-types";

/**
 * Chat page ViewModel.
 *
 * This hook acts as an orchestrator that wires together:
 * - conversation lifecycle management
 * - message fetching and normalization
 * - routing-related side effects
 * - UI-facing handlers (send, retry, reactions, scroll)
 *
 * Individual concerns are intentionally delegated to smaller hooks
 * to keep this file readable and safe to modify.
 */
export const useChatViewModel = (): ChatViewModel => {
  const capabilities = useAppStore((state) => state.capabilities);
  const { t } = useTranslation();
  const messagePageSize = Math.max(
    capabilities.apiPageSizes.messagesPageSizeDefault || 30,
    1,
  );
  const onConversationChangedRef = useRef<(id: string) => void>(() => {});

  // Manages the active conversation id and reacts to server-sent conversation events.
  // This is the single source of truth for "which conversation is active".
  const {
    activeConversationId,
    activeConversationRef,
    skipMessageFetchForIdRef,
    handleDataEvent,
    resetConversation,
  } = useConversationLifecycle({
    scope: "chat",
    onConversationChanged: (id) => onConversationChangedRef.current(id),
  });

  const modelSettings = useChatModelSettingsViewModel({ t });

  // AI SDK hook responsible only for sending messages and receiving streamed responses.
  // Conversation-level concerns (routing, persistence, pagination) are handled elsewhere.
  const { messages, status, sendMessage, regenerate, setMessages, stop } =
    useChat({
      transport: new DefaultChatTransport({
        api: "/api/chat",
        prepareSendMessagesRequest: ({ id, messages, trigger, body }) => ({
          body: {
            ...(body ?? {}),
            id,
            trigger,
            messages: messages.length ? [messages[messages.length - 1]] : [],
          },
        }),
      }),
      onError: (error) => {
        console.error("Chat error:", error);
        const errorText = resolveErrorText(error);
        const errorMessage: UIMessage = {
          id: `err-${crypto.randomUUID()}`,
          role: "assistant",
          parts: [{ type: "text", text: `Error: ${errorText}` }],
          metadata: { isError: true },
        };
        setMessages((prev) => [...prev, errorMessage]);
      },
      // Route server-sent data events to their dedicated handlers.
      // This keeps protocol-specific logic out of the UI layer.
      onData: (data) => {
        if (isConversationDataEvent(data) || isTitleDataEvent(data)) {
          handleDataEvent(data);
          return;
        }
        if (isModelDataEvent(data)) {
          applyModelDataEvent(data);
          return;
        }
      },
    });

  // Resets chat state only when the user explicitly returns to `/chat`
  // from an existing conversation. This avoids UI flicker immediately
  // after sending a message.
  useChatRouteReset({ setMessages, resetConversation });

  // Handles message history loading, pagination, and synchronization
  // with the active conversation id.
  const conversationMessages = useConversationMessages({
    activeConversationId,
    activeConversationRef,
    skipMessageFetchForIdRef,
    messagePageSize,
    messages,
    status,
    setMessages,
  });

  useEffect(() => {
    onConversationChangedRef.current =
      conversationMessages.setMessagesConversationId;
  }, [conversationMessages.setMessagesConversationId]);
  const hasMoreMessages = conversationMessages.hasMoreMessages;

  // Attaches model-related metadata to messages based on streamed events.
  // This is kept separate to avoid coupling message rendering to protocol details.
  const { normalizedMessages, applyModelDataEvent } = useChatModelMetadata({
    messages,
  });

  const messageList = useChatMessageListViewModel({
    messages: normalizedMessages,
  });

  // Controls infinite scroll behavior and preserves scroll position
  // when older messages are loaded.
  const scroll = useChatScrollController({
    hasMoreMessages,
    loadingOlderMessages: conversationMessages.loadingOlderMessages,
    handleLoadOlderMessages: conversationMessages.handleLoadOlderMessages,
  });

  const prompt = useChatInputViewModel({
    t,
    status,
    sendMessage,
    stop,
    activeConversationId,
    model: modelSettings.selectedModelId,
    selectedModelName: modelSettings.selectedModelName,
    modelSelector: modelSettings.modelSelector,
    advancedSettings: modelSettings.advancedSettings,
  });

  // Provides retry logic for assistant messages.
  const { handleRetryMessage } = useChatRetry({
    activeConversationId,
    messagesRef: conversationMessages.messagesRef,
    regenerate,
  });

  // Manages optimistic reaction state and persistence.
  const { reactionById, handleToggleReaction } = useChatMessageReactions({
    activeConversationId,
    messages: normalizedMessages,
  });

  return {
    status,
    scroll,
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
    },
    prompt,
  };
};
