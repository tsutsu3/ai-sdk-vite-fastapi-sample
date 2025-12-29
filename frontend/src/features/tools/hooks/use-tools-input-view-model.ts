import { useCallback, useRef, useState } from "react";
import type { useChat } from "@ai-sdk/react";
import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import type { ChatStatus } from "ai";
import type { ToolsPromptInputViewModel } from "@/features/tools/hooks/tools-view-model-types";
import { buildToolsRequestBody } from "@/features/tools/hooks/tools-view-model-helpers";

type UseToolsInputViewModelArgs = {
  t: (key: string) => string;
  status: ChatStatus;
  sendMessage: ReturnType<typeof useChat>["sendMessage"];
  stop: ReturnType<typeof useChat>["stop"];
  activeConversationId: string;
  toolId: string;
  advancedSettings: ToolsPromptInputViewModel["advancedSettings"];
};

export const useToolsInputViewModel = ({
  t,
  status,
  sendMessage,
  stop,
  activeConversationId,
  toolId,
  advancedSettings,
}: UseToolsInputViewModelArgs): ToolsPromptInputViewModel => {
  const [text, setText] = useState<string>("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(
    (message: PromptInputMessage) => {
      const trimmedText = message.text.trim();
      if (!trimmedText) {
        return;
      }
      const body = buildToolsRequestBody({
        toolId,
        activeConversationId,
        hydeEnabled: advancedSettings.hydeEnabled,
        maxDocuments: advancedSettings.maxDocuments[0],
      });

      sendMessage(
        {
          ...message,
          text: trimmedText,
        },
        { body },
      );
      setText("");
    },
    [
      activeConversationId,
      advancedSettings.hydeEnabled,
      advancedSettings.maxDocuments,
      sendMessage,
      toolId,
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
    advancedSettings,
  };
};
