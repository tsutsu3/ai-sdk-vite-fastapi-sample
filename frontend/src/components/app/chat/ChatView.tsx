import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import type { RefObject } from "react";
import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import type { ChatMessage, ChatModel, ChatStatus } from "@/types/chat";
import { ChatMessageList } from "@/components/app/chat/ChatMessageList";
import { ChatPromptInput } from "@/components/app/chat/ChatPromptInput";

/**
 * Props for the presentational chat view.
 */
export type ChatViewProps = {
  messages: ChatMessage[];
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

/**
 * Pure UI view for the chat page. Handles rendering and event forwarding only.
 */
export const ChatView = ({
  messages,
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
}: ChatViewProps) => {
  return (
    <div className="relative size-full h-full min-h-0">
      <div className="flex flex-col h-full min-h-0 overflow-hidden">
        <Conversation className="flex-1 min-h-0 overflow-y-hidden">
          <ConversationContent className="mx-auto w-full max-w-4xl p-0 px-6 pb-12">
            <ChatMessageList messages={messages} />
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>
        <ChatPromptInput
          text={text}
          status={status}
          models={models}
          selectedModelId={selectedModelId}
          useWebSearch={useWebSearch}
          uploadingAttachments={uploadingAttachments}
          textareaRef={textareaRef}
          onSubmit={onSubmit}
          onTextChange={onTextChange}
          onTranscriptionChange={onTranscriptionChange}
          onToggleWebSearch={onToggleWebSearch}
          onModelChange={onModelChange}
          onAttachmentUploaded={onAttachmentUploaded}
          onAttachmentsRemoved={onAttachmentsRemoved}
          onUploadsInProgress={onUploadsInProgress}
        />
      </div>
    </div>
  );
};
