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
import type { FileUIPart } from "ai";

export type ChatMessageListProps = {
  messages: ChatMessage[];
};

export const ChatMessageList = ({ messages }: ChatMessageListProps) => {
  const { t } = useTranslation();

  return (
    <>
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
    </>
  );
};
