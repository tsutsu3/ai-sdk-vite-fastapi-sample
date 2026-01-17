import { useCallback, useRef, useState } from "react";
import type { useChat } from "@ai-sdk/react";
import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import type { ChatStatus } from "ai";
import type { ChatPromptInputViewModel } from "@/features/chat/hooks/chat-view-model-types";

type UseChatInputViewModelArgs = {
  t: (key: string) => string;
  status: ChatStatus;
  sendMessage: ReturnType<typeof useChat>["sendMessage"];
  stop: ReturnType<typeof useChat>["stop"];
  activeConversationId: string;
  model: string;
  selectedModelName: string;
  modelSelector: ChatPromptInputViewModel["modelSelector"];
  advancedSettings: ChatPromptInputViewModel["advancedSettings"];
};

export const useChatInputViewModel = ({
  t,
  status,
  sendMessage,
  stop,
  activeConversationId,
  model,
  selectedModelName,
  modelSelector,
  advancedSettings,
}: UseChatInputViewModelArgs): ChatPromptInputViewModel => {
  const [text, setText] = useState<string>("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(
    (message: PromptInputMessage) => {
      const trimmedText = message.text.trim();
      if (!trimmedText) {
        return;
      }
      const body = {
        ...(activeConversationId ? { chatId: activeConversationId } : {}),
      };

      sendMessage(
        {
          ...message,
          text: trimmedText,
          metadata: { modelId: model, modelName: selectedModelName },
        },
        { body },
      );
      setText("");
    },
    [
      activeConversationId,
      model,
      sendMessage,
      selectedModelName,
    ],
  );

  const handleTextChange = useCallback((value: string) => {
    setText(value);
  }, []);

  const handleTranscriptionChange = useCallback((value: string) => {
    setText(value);
  }, []);

  const handleSubmitPrompt = useCallback(
    (message: PromptInputMessage) => {
      if (status === "streaming") {
        void stop();
        return;
      }
      handleSubmit(message);
    },
    [handleSubmit, status, stop],
  );

  return {
    t,
    text,
    status,
    textareaRef,
    onSubmitPrompt: handleSubmitPrompt,
    onTextChange: handleTextChange,
    onTranscriptionChange: handleTranscriptionChange,
    modelSelector,
    advancedSettings,
  };
};
