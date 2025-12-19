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
  PromptInputSelect,
  PromptInputSelectContent,
  PromptInputSelectItem,
  PromptInputSelectTrigger,
  PromptInputSelectValue,
  PromptInputSpeechButton,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
} from "@/components/ai-elements/prompt-input";
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  Message,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import type { RefObject } from "react";
import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import type { ChatMessage, ChatModel, ChatStatus } from "@/types/chat";

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
  textareaRef: RefObject<HTMLTextAreaElement | null>;
  onSubmit: (message: PromptInputMessage) => void;
  onTextChange: (value: string) => void;
  onTranscriptionChange: (value: string) => void;
  onToggleWebSearch: () => void;
  onModelChange: (modelId: string) => void;
};

/**
 * Props for the presentational chat view.
 */
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
  textareaRef,
  onSubmit,
  onTextChange,
  onTranscriptionChange,
  onToggleWebSearch,
  onModelChange,
}: ChatViewProps) => {
  return (
    <div className="max-w-4xl mx-auto p-6 relative size-full  h-full">
      <div className="flex flex-col h-full">
        <Conversation>
          <ConversationContent>
            {messages.map((message) => (
              <Message from={message.role} key={message.id}>
                <MessageContent>
                  {message.parts.map((part, i) => {
                    switch (part.type) {
                      case "text":
                        return (
                          <MessageResponse key={`${message.id}-${i}`}>
                            {part.text}
                          </MessageResponse>
                        );
                      default:
                        return null;
                    }
                  })}
                </MessageContent>
              </Message>
            ))}
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>
        <PromptInput onSubmit={onSubmit} className="mt-4" globalDrop multiple>
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
            />
          </PromptInputBody>
          <PromptInputFooter>
            <PromptInputTools>
              <PromptInputActionMenu>
                <PromptInputActionMenuTrigger />
                <PromptInputActionMenuContent>
                  <PromptInputActionAddAttachments />
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
                <span>Search</span>
              </PromptInputButton>
              <PromptInputSelect
                onValueChange={onModelChange}
                value={selectedModelId}
              >
                <PromptInputSelectTrigger>
                  <PromptInputSelectValue />
                </PromptInputSelectTrigger>
                <PromptInputSelectContent>
                  {models.map((model) => (
                    <PromptInputSelectItem key={model.id} value={model.id}>
                      {model.name}
                    </PromptInputSelectItem>
                  ))}
                </PromptInputSelectContent>
              </PromptInputSelect>
            </PromptInputTools>
            <PromptInputSubmit disabled={!text && !status} status={status} />
          </PromptInputFooter>
        </PromptInput>
      </div>
    </div>
  );
};
