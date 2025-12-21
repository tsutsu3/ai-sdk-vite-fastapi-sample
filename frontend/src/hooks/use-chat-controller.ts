import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { useChat } from "@ai-sdk/react";
import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { chatModels } from "@/config/chat-models";
import type { ChatMessage, ChatModel, ChatStatus } from "@/types/chat";
import { useAppStore } from "@/store/app-store";
import { DefaultChatTransport, type FileUIPart } from "ai";

/**
 * Encapsulates chat state, side effects, and handlers for the chat page.
 */
export const useChatController = () => {
  const [text, setText] = useState<string>("");
  const [models, setModels] = useState<ChatModel[]>([]);
  const [model, setModel] = useState<string>("");
  const [useWebSearch, setUseWebSearch] = useState<boolean>(false);
  const [attachmentFileIds, setAttachmentFileIds] = useState<
    Record<string, string>
  >({});
  const [uploadingAttachments, setUploadingAttachments] =
    useState<boolean>(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { id: conversationId } = useParams();
  const navigate = useNavigate();
  const upsertHistoryItem = useAppStore((state) => state.upsertHistoryItem);
  const [localConversationId, setLocalConversationId] = useState<string | null>(
    null
  );
  const skipMessageFetchForIdRef = useRef<string | null>(null);
  const activeConversationId = conversationId ?? localConversationId ?? "";
  const activeConversationIdRef = useRef<string>("");
  const messagesRef = useRef<ChatMessage[]>([]);
  const statusRef = useRef<ChatStatus>("ready");
  const messagesConversationIdRef = useRef<string>("");
  const { messages, status, sendMessage, setMessages } = useChat({
    transport: new DefaultChatTransport({
      api: "/api/chat",
    }),
    onError: (error) => {
      console.error("Chat error:", error);
    },
    onData: (data) => {
      const conversationIdForEvent = activeConversationIdRef.current;
      if (!conversationIdForEvent) {
        return;
      }
      if (
        data &&
        typeof data === "object" &&
        "type" in data &&
        data.type === "data-title"
      ) {
        const titleValue =
          typeof data.data?.title === "string" ? data.data.title.trim() : "";
        if (!titleValue) {
          return;
        }
        upsertHistoryItem({
          name: titleValue,
          url: `/chat/c/${conversationIdForEvent}`,
          updatedAt: new Date().toISOString(),
        });
      }
    },
  });

  useEffect(() => {
    activeConversationIdRef.current = activeConversationId;
  }, [activeConversationId]);

  useEffect(() => {
    let mounted = true;
    const applyModels = (nextModels: ChatModel[]) => {
      setModels(nextModels);
      setModel((current) =>
        nextModels.some((entry) => entry.id === current)
          ? current
          : nextModels[0]?.id ?? ""
      );
    };
    fetch("/api/capabilities")
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (!mounted) {
          return;
        }
        const nextModels =
          payload?.models?.length && Array.isArray(payload.models)
            ? (payload.models as ChatModel[])
            : chatModels;
        applyModels(nextModels);
      })
      .catch(() => {
        if (mounted) {
          applyModels(chatModels);
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    messagesRef.current = messages as ChatMessage[];
  }, [messages]);

  useEffect(() => {
    statusRef.current = status as ChatStatus;
  }, [status]);

  useEffect(() => {
    let mounted = true;
    if (!activeConversationId) {
      setMessages([]);
      messagesConversationIdRef.current = "";
      return () => {
        mounted = false;
      };
    }
    if (skipMessageFetchForIdRef.current === activeConversationId) {
      skipMessageFetchForIdRef.current = null;
      messagesConversationIdRef.current = activeConversationId;
      return () => {
        mounted = false;
      };
    }
    const controller = new AbortController();
    fetch(`/api/conversations/${activeConversationId}/messages`, {
      signal: controller.signal,
    })
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (!mounted) {
          return;
        }
        const nextMessages = Array.isArray(payload?.messages)
          ? (payload.messages as ChatMessage[])
          : [];
        const currentMessages = messagesRef.current;
        const currentStatus = statusRef.current;
        const isSameConversation =
          messagesConversationIdRef.current === activeConversationId;
        if (isSameConversation) {
          if (
            nextMessages.length === 0 &&
            currentMessages.length > 0 &&
            (currentStatus === "submitted" || currentStatus === "streaming")
          ) {
            return;
          }
          if (nextMessages.length < currentMessages.length) {
            return;
          }
        }
        setMessages(nextMessages);
        messagesConversationIdRef.current = activeConversationId;
      })
      .catch(() => {});
    return () => {
      mounted = false;
      controller.abort();
    };
  }, [activeConversationId, setMessages]);

  useEffect(() => {
    if (!conversationId) {
      setLocalConversationId(null);
    }
  }, [conversationId]);

  const handleSubmit = useCallback(
    (message: PromptInputMessage) => {
      const hasText = Boolean(message.text);
      const hasAttachments = Boolean(message.files?.length);
      if (!(hasText || hasAttachments) || uploadingAttachments) {
        return;
      }
      const fileIds = Object.values(attachmentFileIds);
      const baseFiles = message.files ?? [];
      const files: FileUIPart[] =
        fileIds.length && baseFiles.length === fileIds.length
          ? baseFiles.map((file, index) => ({
              ...file,
              providerMetadata: { fileId: fileIds[index] },
            }))
          : baseFiles;
      let nextConversationId = activeConversationId;
      if (!nextConversationId) {
        nextConversationId = `conv-${crypto.randomUUID()}`;
        setLocalConversationId(nextConversationId);
        skipMessageFetchForIdRef.current = nextConversationId;
        activeConversationIdRef.current = nextConversationId;
        messagesConversationIdRef.current = nextConversationId;
        navigate(`/chat/c/${nextConversationId}`);
        upsertHistoryItem({
          name: "New Chat",
          url: `/chat/c/${nextConversationId}`,
          updatedAt: new Date().toISOString(),
        });
      }

      // TODO: Use Base64-encoded data for display, and use the storage `fileId` for sending.
      // The `fileId` can be resolved to the actual file from storage when needed.
      const body = {
        model,
        webSearch: useWebSearch,
        ...(fileIds.length ? { fileIds } : {}),
        ...(nextConversationId ? { conversationId: nextConversationId } : {}),
      };
      sendMessage(
        {
          text: message.text,
          files,
        },
        { body }
      );
      setText("");
      setAttachmentFileIds({});
    },
    [
      attachmentFileIds,
      activeConversationId,
      model,
      navigate,
      sendMessage,
      upsertHistoryItem,
      uploadingAttachments,
      useWebSearch,
    ]
  );

  const handleTextChange = useCallback((value: string) => {
    setText(value);
  }, []);

  const handleTranscriptionChange = useCallback((value: string) => {
    setText(value);
  }, []);

  const handleModelChange = useCallback((value: string) => {
    setModel(value);
  }, []);

  const handleToggleWebSearch = useCallback(() => {
    setUseWebSearch((prev) => !prev);
  }, []);

  const handleAttachmentUploaded = useCallback(
    (attachmentId: string, fileId: string) => {
      setAttachmentFileIds((prev) => ({ ...prev, [attachmentId]: fileId }));
    },
    []
  );

  const handleAttachmentsRemoved = useCallback((attachmentIds: string[]) => {
    if (!attachmentIds.length) {
      return;
    }
    setAttachmentFileIds((prev) => {
      const next = { ...prev };
      for (const id of attachmentIds) {
        delete next[id];
      }
      return next;
    });
  }, []);

  const handleUploadsInProgress = useCallback((count: number) => {
    setUploadingAttachments(count > 0);
  }, []);

  return {
    models,
    messages: messages as ChatMessage[],
    status: status as ChatStatus,
    text,
    selectedModelId: model,
    useWebSearch,
    uploadingAttachments,
    textareaRef,
    onSubmit: handleSubmit,
    onTextChange: handleTextChange,
    onTranscriptionChange: handleTranscriptionChange,
    onModelChange: handleModelChange,
    onToggleWebSearch: handleToggleWebSearch,
    onAttachmentUploaded: handleAttachmentUploaded,
    onAttachmentsRemoved: handleAttachmentsRemoved,
    onUploadsInProgress: handleUploadsInProgress,
  };
};
