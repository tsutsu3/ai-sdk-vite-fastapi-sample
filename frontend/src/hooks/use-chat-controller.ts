import { useCallback, useRef, useState } from "react";
import { useChat } from "@ai-sdk/react";
import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { chatModels } from "@/config/chat-models";
import type { ChatMessage, ChatStatus } from "@/types/chat";

/**
 * Encapsulates chat state, side effects, and handlers for the chat page.
 */
export const useChatController = () => {
  const [text, setText] = useState<string>("");
  const [model, setModel] = useState<string>(chatModels[0]?.id ?? "");
  const [useWebSearch, setUseWebSearch] = useState<boolean>(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { messages, status, sendMessage } = useChat();

  const handleSubmit = useCallback(
    (message: PromptInputMessage) => {
      const hasText = Boolean(message.text);
      const hasAttachments = Boolean(message.files?.length);
      if (!(hasText || hasAttachments)) {
        return;
      }
      sendMessage(
        {
          text: message.text || "Sent with attachments",
          files: message.files,
        },
        {
          body: {
            model,
            webSearch: useWebSearch,
          },
        }
      );
      setText("");
    },
    [model, sendMessage, useWebSearch]
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

  return {
    models: chatModels,
    messages: messages as ChatMessage[],
    status: status as ChatStatus,
    text,
    selectedModelId: model,
    useWebSearch,
    textareaRef,
    onSubmit: handleSubmit,
    onTextChange: handleTextChange,
    onTranscriptionChange: handleTranscriptionChange,
    onModelChange: handleModelChange,
    onToggleWebSearch: handleToggleWebSearch,
  };
};
