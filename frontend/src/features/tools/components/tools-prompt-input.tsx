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
import { ToolsAdvancedSettingsPopover } from "@/features/tools/components/tools-advanced-settings-popover";
import type { ToolsPromptInputViewModel } from "@/features/tools/hooks/tools-view-model-types";
import { cn } from "@/lib/utils";

export type ToolsPromptInputProps = {
  viewModel: ToolsPromptInputViewModel;
  className?: string;
};

export const ToolsPromptInput = ({
  viewModel,
  className,
}: ToolsPromptInputProps) => {
  const {
    t,
    text,
    status,
    textareaRef,
    onTextChange,
    onTranscriptionChange,
    onSubmitPrompt,
    advancedSettings,
  } = viewModel;

  return (
    <PromptInput
      onSubmit={onSubmitPrompt}
      className={cn(
        "bg-background sticky bottom-0 mx-auto w-full max-w-3xl px-3 pb-6",
        className,
      )}
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
