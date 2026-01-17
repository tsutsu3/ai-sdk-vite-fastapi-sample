import { PromptInputShell } from "@/components/app/chat/prompt-input-shell";
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
    <PromptInputShell
      text={text}
      status={status}
      textareaRef={textareaRef}
      placeholder={t("chatPromptPlaceholder")}
      addAttachmentsLabel={t("addPhotosOrFiles")}
      onSubmit={onSubmitPrompt}
      onTextChange={onTextChange}
      onTranscriptionChange={onTranscriptionChange}
      tools={<ToolsAdvancedSettingsPopover viewModel={advancedSettings} />}
      className={cn(className)}
    />
  );
};
