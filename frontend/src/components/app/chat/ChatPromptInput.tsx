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
import type { RefObject } from "react";
import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import type { ChatModel, ChatStatus } from "@/types/chat";
import { useTranslation } from "react-i18next";
import { AttachmentUploadBridge } from "@/components/app/chat/AttachmentUploadBridge";
import { ChatModelSelector } from "@/components/app/chat/ChatModelSelector";

export type ChatPromptInputProps = {
  text: string;
  status: ChatStatus;
  models: ChatModel[];
  selectedModelId: string;
  useWebSearch: boolean;
  uploadingAttachments: boolean;
  textareaRef: RefObject<HTMLTextAreaElement | null>;
  onSubmit: (message: PromptInputMessage) => void;
  onTextChange: (value: string) => void;
  onTranscriptionChange: (value: string) => void;
  onToggleWebSearch: () => void;
  onModelChange: (modelId: string) => void;
  onAttachmentUploaded: (attachmentId: string, fileId: string) => void;
  onAttachmentsRemoved: (attachmentIds: string[]) => void;
  onUploadsInProgress: (count: number) => void;
};

export const ChatPromptInput = ({
  text,
  status,
  models,
  selectedModelId,
  useWebSearch,
  uploadingAttachments,
  textareaRef,
  onSubmit,
  onTextChange,
  onTranscriptionChange,
  onToggleWebSearch,
  onModelChange,
  onAttachmentUploaded,
  onAttachmentsRemoved,
  onUploadsInProgress,
}: ChatPromptInputProps) => {
  const { t } = useTranslation();

  return (
    <PromptInput
      onSubmit={onSubmit}
      className="sticky bottom-0 pb-6 bg-background mx-auto w-full max-w-4xl px-3"
      globalDrop
      multiple
    >
      <AttachmentUploadBridge
        onUploaded={onAttachmentUploaded}
        onRemoved={onAttachmentsRemoved}
        onUploadCountChange={onUploadsInProgress}
      />
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
          <ChatModelSelector
            models={models}
            selectedModelId={selectedModelId}
            onModelChange={onModelChange}
          />
        </PromptInputTools>
        <PromptInputSubmit
          disabled={(!text && !status) || uploadingAttachments}
          status={status}
        />
      </PromptInputFooter>
    </PromptInput>
  );
};
