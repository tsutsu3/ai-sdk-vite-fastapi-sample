import { GlobeIcon } from "lucide-react";
import {
  PromptInput,
  PromptInputActionAddAttachments,
  PromptInputActionMenu,
  PromptInputActionMenuContent,
  PromptInputActionMenuTrigger,
  PromptInputAttachment,
  PromptInputAttachments,
  PromptInputBody,
  PromptInputButton,
  PromptInputFooter,
  PromptInputHeader,
  PromptInputSpeechButton,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
} from "@/components/ai-elements/prompt-input";
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
    <PromptInput
      onSubmit={onSubmitPrompt}
      className="bg-background sticky bottom-0 mx-auto w-full max-w-4xl px-3 pb-6"
      globalDrop
      multiple
    >
      <PromptInputHeader>
        <PromptInputAttachments>
          {(attachment) => <PromptInputAttachment data={attachment} />}
        </PromptInputAttachments>
      </PromptInputHeader>
      <PromptInputBody>
        <PromptInputTextarea
          onChange={(event) => onTextChange(event.target.value)}
          ref={textareaRef}
          value={text}
          placeholder={t("chatPromptPlaceholder")}
        />
      </PromptInputBody>
      <PromptInputFooter>
        <PromptInputTools>
          <PromptInputActionMenu>
            <PromptInputActionMenuTrigger />
            <PromptInputActionMenuContent>
              <PromptInputActionAddAttachments label={t("addPhotosOrFiles")} />
            </PromptInputActionMenuContent>
          </PromptInputActionMenu>
          <PromptInputSpeechButton
            onTranscriptionChange={onTranscriptionChange}
            textareaRef={textareaRef}
          />
          <PromptInputButton
            onClick={onToggleWebSearch}
            variant={useWebSearch ? "default" : "ghost"}
          >
            <GlobeIcon size={16} />
            <span>{t("search")}</span>
          </PromptInputButton>
          <ChatModelSelector viewModel={modelSelector} />
          <ChatAdvancedSettingsPopover viewModel={advancedSettings} />
        </PromptInputTools>
        <PromptInputSubmit
          disabled={!text && !status}
          status={status}
        />
      </PromptInputFooter>
    </PromptInput>
  );
};
