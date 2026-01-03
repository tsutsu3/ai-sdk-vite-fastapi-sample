import { GlobeIcon } from "lucide-react";
import { PromptInputButton } from "@/components/ai-elements/prompt-input";
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
    useWebSearch,
    textareaRef,
    onTextChange,
    onTranscriptionChange,
    onToggleWebSearch,
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
          <PromptInputButton
            onClick={onToggleWebSearch}
            variant={useWebSearch ? "default" : "ghost"}
          >
            <GlobeIcon size={16} />
            <span>{t("search")}</span>
          </PromptInputButton>
          <ChatModelSelector viewModel={modelSelector} />
          <ChatAdvancedSettingsPopover viewModel={advancedSettings} />
        </>
      }
    />
  );
};
