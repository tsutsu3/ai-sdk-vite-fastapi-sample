import type { ReactNode } from "react";
import type { ChatStatus } from "ai";
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
  type PromptInputMessage,
} from "@/components/ai-elements/prompt-input";
import { cn } from "@/lib/utils";

export type PromptInputShellProps = {
  text: string;
  status: ChatStatus;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  placeholder: string;
  addAttachmentsLabel: string;
  onSubmit: (message: PromptInputMessage) => void;
  onTextChange: (value: string) => void;
  onTranscriptionChange: (value: string) => void;
  tools?: ReactNode;
  className?: string;
};

export const PromptInputShell = ({
  text,
  status,
  textareaRef,
  placeholder,
  addAttachmentsLabel,
  onSubmit,
  onTextChange,
  onTranscriptionChange,
  tools,
  className,
}: PromptInputShellProps) => (
  <PromptInput
    onSubmit={onSubmit}
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
        placeholder={placeholder}
      />
    </PromptInputBody>
    <PromptInputFooter>
      <PromptInputTools>
        <PromptInputActionMenu>
        <PromptInputActionMenuTrigger />
        <PromptInputActionMenuContent>
          <PromptInputActionAddAttachments label={addAttachmentsLabel} />
        </PromptInputActionMenuContent>
      </PromptInputActionMenu>
        <PromptInputSpeechButton
          onTranscriptionChange={onTranscriptionChange}
          textareaRef={textareaRef}
        />
        {tools}
      </PromptInputTools>
      <PromptInputSubmit disabled={!text && !status} status={status} />
    </PromptInputFooter>
  </PromptInput>
);
