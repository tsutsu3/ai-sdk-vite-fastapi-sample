import {
  CheckIcon,
  CopyIcon,
  // RefreshCcwIcon,
  ThumbsDownIcon,
  ThumbsUpIcon,
  BotIcon,
} from "lucide-react";
import {
  Message,
  MessageAction,
  MessageActions,
  MessageAttachment,
  MessageAttachments,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
// import type { ChatStatus, FileUIPart } from "ai";
import type { FileUIPart } from "ai";
import {
  Reasoning,
  ReasoningContent,
  ReasoningTrigger,
} from "@/components/ai-elements/reasoning";
import { AlertTriangleIcon } from "lucide-react";
import type { ChatMessageListViewModel } from "@/features/chat/hooks/use-chat-view-model";

export type ChatMessageListProps = {
  viewModel: ChatMessageListViewModel;
};

export const ChatMessageList = ({ viewModel }: ChatMessageListProps) => {
  const {
    messages,
    models,
    reactionById,
    onToggleReaction,
    // onRetryMessage,
    t,
    copiedMessageId,
    onCopyMessage,
  } = viewModel;

  return (
    <>
      {messages.map((message) => {
        const modelId = message.metadata?.modelId;
        const modelName = modelId
          ? models.find((model) => model.id === modelId)?.name || modelId
          : null;

        return (
          <Message from={message.role} key={message.id} className="pt-6">
            <MessageContent
              className={message.metadata?.isError ? "overflow-visible" : undefined}
            >
              {message.role === "assistant" && modelName && (
                <div className="text-muted-foreground mb-2 flex items-center text-sm">
                  <BotIcon className="mr-2 size-4" />
                  <span>Model: {modelName}</span>
                </div>
              )}
              {message.metadata?.isError ? (
                <div className="flex gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-destructive text-sm">
                  <AlertTriangleIcon className="mt-0.5 size-4 shrink-0" />
                  <div className="min-w-0">
                    {message.parts
                      .filter((part) => part.type === "text")
                      .map((part, i) => (
                        <MessageResponse key={`${message.id}-error-${i}`}>
                          {part.text}
                        </MessageResponse>
                      ))}
                  </div>
                </div>
              ) : (
                message.parts.map((part, i) => {
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
                    case "reasoning":
                      return (
                        <Reasoning
                          key={`${message.id}-${i}`}
                          className="w-full"
                          isStreaming={
                            // status === "streaming" &&
                            part.state === "streaming" &&
                            i === message.parts.length - 1 &&
                            message.id === messages.at(-1)?.id
                          }
                        >
                          <ReasoningTrigger
                            getThinkingMessage={(isStreaming) =>
                              isStreaming
                                ? `${t("webSearchInProgress")}`
                                : t("webSearchCompleted")
                            }
                          />
                          <ReasoningContent>{part.text}</ReasoningContent>
                        </Reasoning>
                      );
                    default:
                      return null;
                  }
                })
              )}
            </MessageContent>
            {/* {message.role === "assistant" && message.versions && ( */}
            {message.role === "assistant" && (
              <MessageActions>
                {/* TODO: message branch retry */}
                {/* <MessageAction
                  label="Retry"
                  onClick={() => onRetryMessage(message.id)}
                  tooltip={t("regenerateThisResponse")}
                >
                  <RefreshCcwIcon className="size-4" />
                </MessageAction> */}
                {reactionById[message.id] !== "dislike" && (
                  <MessageAction
                    label="Like"
                    onClick={() => onToggleReaction(message.id, "like")}
                    tooltip={t("likeThisResponse")}
                  >
                    <ThumbsUpIcon
                      className="size-4"
                      fill={
                        reactionById[message.id] === "like"
                          ? "currentColor"
                          : "none"
                      }
                    />
                  </MessageAction>
                )}
                {reactionById[message.id] !== "like" && (
                  <MessageAction
                    label="Dislike"
                    onClick={() => onToggleReaction(message.id, "dislike")}
                    tooltip={t("dislikeThisResponse")}
                  >
                    <ThumbsDownIcon
                      className="size-4"
                      fill={
                        reactionById[message.id] === "dislike"
                          ? "currentColor"
                          : "none"
                      }
                    />
                  </MessageAction>
                )}
                <MessageAction
                  label="Copy"
                  onClick={() => onCopyMessage(message)}
                  tooltip={t("copyToClipboard")}
                >
                  {copiedMessageId === message.id ? (
                    <CheckIcon className="size-4" />
                  ) : (
                    <CopyIcon className="size-4" />
                  )}
                </MessageAction>
              </MessageActions>
            )}
          </Message>
        );
      })}
    </>
  );
};
