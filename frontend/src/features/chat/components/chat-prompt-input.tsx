import { PromptInputShell } from "@/components/app/chat/prompt-input-shell";
import { ChatModelSelector } from "./chat-model-selector";
import { ChatAdvancedSettingsPopover } from "./chat-advanced-settings-popover";
import type { ChatPromptInputViewModel } from "@/features/chat/hooks/use-chat-view-model";

export type ChatPromptInputProps = {
  viewModel: ChatPromptInputViewModel;
};

export const ChatPromptInput = ({
  viewModel,
}: ChatPromptInputProps) => {
  const {
    t,
    text,
    status,
    textareaRef,
    onTextChange,
    onTranscriptionChange,
    onSubmitPrompt,
    modelSelector,
    advancedSettings,
  } = viewModel;

  return (
    <PromptInputShell
      text={text}
      status={status}
      textareaRef={textareaRef}
      placeholder={t("chatPromptPlaceholder")}
      addAttachmentsLabel={t("addPhotosOrFiles")}
      onSubmit={onSubmitPrompt}
      onTextChange={onTextChange}
      onTranscriptionChange={onTranscriptionChange}
      tools={
        <>
          <ChatModelSelector viewModel={modelSelector} />
          <ChatAdvancedSettingsPopover viewModel={advancedSettings} />
        </>
      }
    />
  );
};
