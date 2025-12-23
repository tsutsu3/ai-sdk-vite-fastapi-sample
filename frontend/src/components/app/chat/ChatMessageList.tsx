import { CopyIcon, RefreshCcwIcon, ThumbsDownIcon, ThumbsUpIcon } from "lucide-react";
import type { ChatMessage } from "@/types/chat";
import {
  Message,
  MessageAction,
  MessageActions,
  MessageAttachment,
  MessageAttachments,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import { useTranslation } from "react-i18next";
import type { ChatStatus, FileUIPart } from "ai";
import { Reasoning, ReasoningContent, ReasoningTrigger } from "@/components/ai-elements/reasoning";

export type ChatMessageListProps = {
  messages: ChatMessage[];
  status: ChatStatus;
};

export const ChatMessageList = ({ messages, status }: ChatMessageListProps) => {
  const { t } = useTranslation();
  const lastMessageId = messages.at(-1)?.id;

  return (
    <div className="p-6">
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
                case "reasoning":
                  console.log(message.parts);
                  return (
                    <Reasoning
                      key={`${message.id}-${i}`}
                      className="w-full"
                      isStreaming={
                        // web検索完了後、AIレスポンス開始までにしばらく時間があるるのでいい感じにしたい
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
            })}
          </MessageContent>
          {/* {message.role === "assistant" && message.versions && ( */}
          {message.role === "assistant" && message.id === lastMessageId &&(
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
    </div>
  );
};
