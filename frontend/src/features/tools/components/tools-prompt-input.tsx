import {
  PromptInput,
  PromptInputActionAddAttachments,
  PromptInputActionMenu,
  PromptInputActionMenuContent,
  PromptInputActionMenuTrigger,
  PromptInputAttachment,
  PromptInputAttachments,
  PromptInputBody,
  PromptInputFooter,
  PromptInputHeader,
  PromptInputSpeechButton,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
} from "@/components/ai-elements/prompt-input";
import { ChatModelSelector } from "@/features/chat/components/chat-model-selector";
import { ToolsAdvancedSettingsPopover } from "@/features/tools/components/tools-advanced-settings-popover";
import type { ToolsPromptInputViewModel } from "@/features/tools/hooks/tools-view-model-types";

export type ToolsPromptInputProps = {
  viewModel: ToolsPromptInputViewModel;
};

export const ToolsPromptInput = ({ viewModel }: ToolsPromptInputProps) => {
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
          <ChatModelSelector viewModel={modelSelector} />
          <ToolsAdvancedSettingsPopover viewModel={advancedSettings} />
        </PromptInputTools>
        <PromptInputSubmit
          disabled={!text && !status}
          status={status}
        />
      </PromptInputFooter>
    </PromptInput>
  );
};
