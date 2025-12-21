import { CheckIcon, CopyIcon, GlobeIcon, RefreshCcwIcon, ThumbsDownIcon, ThumbsUpIcon } from "lucide-react";
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
  usePromptInputAttachments,
} from "@/components/ai-elements/prompt-input";
import {
  ModelSelector,
  ModelSelectorContent,
  ModelSelectorEmpty,
  ModelSelectorGroup,
  ModelSelectorInput,
  ModelSelectorItem,
  ModelSelectorList,
  ModelSelectorLogo,
  ModelSelectorLogoGroup,
  ModelSelectorName,
  ModelSelectorTrigger,
} from "@/components/ai-elements/model-selector";
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  Message,
  MessageAction,
  MessageActions,
  MessageAttachment,
  MessageAttachments,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import {  useEffect, useMemo, useRef, useState } from "react";
import type { RefObject } from "react";
import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import type { ChatMessage, ChatModel, ChatStatus } from "@/types/chat";
import { Button } from "@/components/ui/button";
import { useTranslation } from "react-i18next";
import {type FileUIPart}  from "ai";

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

const AttachmentUploadBridge = ({
  onUploaded,
  onRemoved,
  onUploadCountChange,
}: {
  onUploaded: (attachmentId: string, fileId: string) => void;
  onRemoved: (attachmentIds: string[]) => void;
  onUploadCountChange: (count: number) => void;
}) => {
  const attachments = usePromptInputAttachments();
  const uploadingIds = useRef<Set<string>>(new Set());
  const uploadedIds = useRef<Set<string>>(new Set());
  const knownIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    const currentIds = new Set(attachments.files.map((file) => file.id));
    const removed: string[] = [];
    for (const id of knownIds.current) {
      if (!currentIds.has(id)) {
        removed.push(id);
        uploadedIds.current.delete(id);
        uploadingIds.current.delete(id);
      }
    }
    if (removed.length) {
      onRemoved(removed);
    }
    knownIds.current = currentIds;
  }, [attachments.files, onRemoved]);

  useEffect(() => {
    let cancelled = false;
    const uploadNew = async () => {
      const pending = attachments.files.filter(
        (file) =>
          !uploadingIds.current.has(file.id) &&
          !uploadedIds.current.has(file.id)
      );
      if (!pending.length) {
        onUploadCountChange(0);
        return;
      }
      onUploadCountChange(pending.length);
      for (const file of pending) {
        uploadingIds.current.add(file.id);
        onUploadCountChange(uploadingIds.current.size);
        try {
          const response = await fetch(file.url);
          const blob = await response.blob();
          const formData = new FormData();
          formData.append("file", blob, file.filename || "upload.bin");
          const uploadResponse = await fetch("/api/file", {
            method: "POST",
            body: formData,
          });
          if (!uploadResponse.ok) {
            throw new Error("File upload failed");
          }
          const payload = await uploadResponse.json();
          if (!cancelled && payload?.fileId) {
            onUploaded(file.id, payload.fileId as string);
            uploadedIds.current.add(file.id);
          }
        } catch {
          if (!cancelled) {
            onRemoved([file.id]);
          }
        } finally {
          uploadingIds.current.delete(file.id);
          onUploadCountChange(uploadingIds.current.size);
        }
      }
    };
    uploadNew();
    return () => {
      cancelled = true;
    };
  }, [attachments.files, onRemoved, onUploadCountChange, onUploaded]);

  return null;
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
  const {t} = useTranslation();
  const [open, setOpen] = useState(false);
  const selectedModelData = useMemo(
    () => models.find((model) => model.id === selectedModelId),
    [models, selectedModelId]
  );
  const chefs = useMemo(
    () => Array.from(new Set(models.map((model) => model.chef))),
    [models]
  );

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
                      case "file":
                        return (
                          // TODO: use image url
                          <MessageAttachments className="mb-2">
                              <MessageAttachment
                                data={part as FileUIPart}
                                key={`${message.id}-attachment-${i}`}
                              />
                          </MessageAttachments>
                        );
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
                {/* {message.role === "assistant" && message.versions && ( */}
                {message.role === "assistant" && (
                  <MessageActions>
                    <MessageAction
                      label="Retry"
                      // onClick={handleRetry}
                      // tooltip="Regenerate this response"
                      tooltip={t("regenerateThisResponse")}
                    >
                      <RefreshCcwIcon className="size-4" />
                    </MessageAction>
                    <MessageAction
                      label="Like"
                      // onClick={() =>
                      //   setLiked((prev) => ({
                      //     ...prev,
                      //     [message.id]: !prev[message.id],
                      //   }))
                      // }
                      // tooltip="Like this response"
                      tooltip={t("likeThisResponse")}
                    >
                      <ThumbsUpIcon
                        className="size-4"
                        // fill={liked[message.id] ? "currentColor" : "none"}
                      />
                    </MessageAction>
                    <MessageAction
                      label="Dislike"
                      // onClick={() =>
                      //   setDisliked((prev) => ({
                      //     ...prev,
                      //     [message.id]: !prev[message.id],
                      //   }))
                      // }
                      // tooltip="Dislike this response"
                      tooltip={t("dislikeThisResponse")}
                    >
                      <ThumbsDownIcon
                        className="size-4"
                        // fill={disliked[message.id] ? "currentColor" : "none"}
                      />
                    </MessageAction>
                    <MessageAction
                      label="Copy"
                      // onClick={() => handleCopy(message.content || "")}
                      // tooltip="Copy to clipboard"
                      tooltip={t("copyToClipboard")}
                    >
                      <CopyIcon className="size-4" />
                    </MessageAction>
                  </MessageActions>
                )}
              </Message>
            ))}
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>
        <PromptInput onSubmit={onSubmit} className="mt-4" globalDrop multiple>
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
                  <PromptInputActionAddAttachments
                    label={t("addPhotosOrFiles")}
                  />
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
              <ModelSelector onOpenChange={setOpen} open={open}>
                <ModelSelectorTrigger asChild>
                  <Button
                    className="w-[200px] justify-between"
                    variant="outline"
                  >
                    {selectedModelData?.chefSlug && (
                      <ModelSelectorLogo
                        provider={selectedModelData.chefSlug}
                      />
                    )}
                    {selectedModelData?.name ? (
                      <ModelSelectorName>
                        {selectedModelData.name}
                      </ModelSelectorName>
                    ) : (
                      <ModelSelectorName>Select model</ModelSelectorName>
                    )}
                  </Button>
                </ModelSelectorTrigger>
                <ModelSelectorContent>
                  <ModelSelectorInput placeholder={t("searchModels")} />
                  <ModelSelectorList>
                    <ModelSelectorEmpty>No models found.</ModelSelectorEmpty>
                    {chefs.map((chef) => (
                      <ModelSelectorGroup heading={chef} key={chef}>
                        {models
                          .filter((model) => model.chef === chef)
                          .map((model) => (
                            <ModelSelectorItem
                              key={model.id}
                              onSelect={() => {
                                onModelChange(model.id);
                                setOpen(false);
                              }}
                              value={model.id}
                            >
                              <ModelSelectorLogo provider={model.chefSlug} />
                              <ModelSelectorName>
                                {model.name}
                              </ModelSelectorName>
                              <ModelSelectorLogoGroup>
                                {model.providers.map((provider) => (
                                  <ModelSelectorLogo
                                    key={provider}
                                    provider={provider}
                                  />
                                ))}
                              </ModelSelectorLogoGroup>
                              {selectedModelId === model.id ? (
                                <CheckIcon className="ml-auto size-4" />
                              ) : (
                                <div className="ml-auto size-4" />
                              )}
                            </ModelSelectorItem>
                          ))}
                      </ModelSelectorGroup>
                    ))}
                  </ModelSelectorList>
                </ModelSelectorContent>
              </ModelSelector>
            </PromptInputTools>
            <PromptInputSubmit
              disabled={(!text && !status) || uploadingAttachments}
              status={status}
            />
          </PromptInputFooter>
        </PromptInput>
      </div>
    </div>
  );
};
