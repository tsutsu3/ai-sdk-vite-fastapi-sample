import {
  BotIcon,
  CheckIcon,
  CopyIcon,
  CpuIcon,
  SearchIcon,
  // RefreshCcwIcon,
  ThumbsDownIcon,
  ThumbsUpIcon,
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
import {
  ChainOfThought,
  ChainOfThoughtContent,
  ChainOfThoughtHeader,
  ChainOfThoughtSearchResult,
  ChainOfThoughtSearchResults,
  ChainOfThoughtStep,
} from "@/components/ai-elements/chain-of-thought";
import {
  Source,
  Sources,
  SourcesContent,
  SourcesTrigger,
} from "@/components/ai-elements/sources";
// import type { ChatStatus, FileUIPart } from "ai";
import type { FileUIPart } from "ai";
import { AlertTriangleIcon } from "lucide-react";
import type { ChatMessageListViewModel } from "@/features/chat/hooks/use-chat-view-model";
import { memo, useEffect, useState } from "react";
import type { RagProgressStep } from "@/shared/types/rag-progress";
import type { RagSourceItem } from "@/shared/types/rag-sources";

export type ChatMessageListProps = {
  viewModel: ChatMessageListViewModel;
};

const MessageRagProgress = memo(({ steps }: { steps: RagProgressStep[] }) => {
  const isComplete = steps.length > 0 && steps.every((step) => step.status === "complete");
  const [open, setOpen] = useState(!isComplete);
  useEffect(() => {
    if (isComplete) {
      setOpen(false);
    } else {
      setOpen(true);
    }
  }, [isComplete]);
  if (!steps.length) {
    return null;
  }
  return (
    <ChainOfThought open={open} onOpenChange={setOpen}>
      <ChainOfThoughtHeader>RAG Progress</ChainOfThoughtHeader>
      <ChainOfThoughtContent>
          {steps.map((step) => {
            const isSearch = step.id === "search";
            const isAnswer = step.id === "answer";
            const resultCount =
              typeof step.resultCount === "number" ? step.resultCount : null;
          const resultTitles = Array.isArray(step.resultTitles)
            ? step.resultTitles.filter((title) => typeof title === "string")
            : [];
          const showResults = isSearch && (resultCount !== null || resultTitles.length);

            return (
              <ChainOfThoughtStep
                key={step.id}
                icon={isSearch ? SearchIcon : isAnswer ? CpuIcon : undefined}
                label={step.label}
                description={step.description}
                status={step.status}
              >
              {showResults && (
                <ChainOfThoughtSearchResults>
                  {resultTitles.map((title, index) => (
                    <ChainOfThoughtSearchResult
                      key={`${step.id}-title-${index}`}
                    >
                      {title}
                    </ChainOfThoughtSearchResult>
                  ))}
                </ChainOfThoughtSearchResults>
              )}
            </ChainOfThoughtStep>
          );
        })}
      </ChainOfThoughtContent>
    </ChainOfThought>
  );
});

MessageRagProgress.displayName = "MessageRagProgress";

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
    ragProgressByMessageId,
    ragSourcesByMessageId,
  } = viewModel;

  const resolveRagProgressSteps = (
    message: typeof messages[number],
  ): RagProgressStep[] => {
    const fromMap = ragProgressByMessageId?.[message.id];
    if (Array.isArray(fromMap) && fromMap.length > 0) {
      return fromMap;
    }
    const ragPart = message.parts.find((part) => part.type === "rag-progress");
    if (!ragPart || typeof ragPart.text !== "string") {
      return [];
    }
    try {
      const parsed = JSON.parse(ragPart.text);
      if (!Array.isArray(parsed)) {
        return [];
      }
      return parsed.filter(
        (item: RagProgressStep) =>
          item &&
          typeof item.id === "string" &&
          typeof item.label === "string",
      );
    } catch {
      return [];
    }
  };

  const resolveRagSources = (
    message: typeof messages[number],
  ): RagSourceItem[] => {
    const fromMap = ragSourcesByMessageId?.[message.id];
    if (Array.isArray(fromMap) && fromMap.length > 0) {
      return fromMap;
    }
    const ragPart = message.parts.find((part) => part.type === "rag-sources");
    if (!ragPart || typeof ragPart.text !== "string") {
      return [];
    }
    try {
      const parsed = JSON.parse(ragPart.text);
      if (!Array.isArray(parsed)) {
        return [];
      }
      return parsed.filter(
        (item: RagSourceItem) =>
          item &&
          typeof item.id === "string" &&
          typeof item.title === "string",
      );
    } catch {
      return [];
    }
  };

  const normalizeSourceKey = (value: string) =>
    value.trim().replace(/\\/g, "/").toLowerCase();

  const normalizeSourceUrl = (value?: string) => {
    if (!value) {
      return "";
    }
    const normalized = value.replace(/\\/g, "/");
    if (/^https?:\/\//i.test(normalized) || normalized.startsWith("/")) {
      return normalized;
    }
    return `/${normalized}`;
  };

  const buildSourceIndexMap = (sources: RagSourceItem[]) => {
    const indexByKey = new Map<string, number>();
    sources.forEach((source, index) => {
      if (source.url) {
        indexByKey.set(normalizeSourceKey(source.url), index);
      }
      if (source.title) {
        indexByKey.set(normalizeSourceKey(source.title), index);
      }
    });
    return indexByKey;
  };

  const renderTextWithSourceLinks = (
    text: string,
    sources: RagSourceItem[],
  ): string => {
    if (!text || sources.length === 0) {
      return text;
    }
    const indexByKey = buildSourceIndexMap(sources);
    const regex = /source:\s*([^\s\)\]\n）。,,]+(?:\.[a-z0-9]+)?)/gi;
    let cursor = 0;
    let output = "";
    let match: RegExpExecArray | null;
    while ((match = regex.exec(text)) !== null) {
      const rawPath = match[1];
      const key = normalizeSourceKey(rawPath.replace(/[)\]）。,]+$/g, ""));
      const index = indexByKey.get(key);
      output += text.slice(cursor, match.index);
      if (index !== undefined && sources[index]?.url) {
        const url = normalizeSourceUrl(sources[index].url);
        output += url ? `[${index + 1}](${url})` : `[${index + 1}]`;
      } else {
        output += match[0];
      }
      cursor = match.index + match[0].length;
    }
    if (cursor < text.length) {
      output += text.slice(cursor);
    }
    return output || text;
  };

  return (
    <>
      {messages.map((message) => {
        const modelId = message.metadata?.modelId;
        const modelName = modelId
          ? models.find((model) => model.id === modelId)?.name || modelId
          : null;
        const hasTextStarted = message.parts.some((part) => part.type === "text");
        const ragSteps = resolveRagProgressSteps(message);
        const ragSources = resolveRagSources(message);
        const messageParts = message.parts.filter(
          (part) => part.type !== "rag-progress" && part.type !== "rag-sources",
        );

        return (
          <Message from={message.role} key={message.id} className="pt-6">
            <MessageContent
              className={message.metadata?.isError ? "overflow-visible" : undefined}
            >
              {message.role === "assistant" && hasTextStarted && modelName && (
                <div className="text-muted-foreground mb-2 flex items-center text-sm">
                  <BotIcon className="mr-2 size-4" />
                  <span>Model: {modelName}</span>
                </div>
              )}
              {message.role === "assistant" && ragSteps.length > 0 && (
                <div className="mb-3">
                  <MessageRagProgress steps={ragSteps} />
                </div>
              )}
              {message.metadata?.isError ? (
                <div className="flex gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-destructive text-sm">
                  <AlertTriangleIcon className="mt-0.5 size-4 shrink-0" />
                  <div className="min-w-0">
                    {messageParts
                      .filter((part) => part.type === "text")
                      .map((part, i) => (
                        <MessageResponse key={`${message.id}-error-${i}`}>
                          {part.text}
                        </MessageResponse>
                      ))}
                  </div>
                </div>
              ) : (
                messageParts.map((part, i) => {
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
                    case "text": {
                      const text = part.text ?? "";
                      return (
                        <MessageResponse key={`${message.id}-${i}`}>
                          {message.role === "assistant"
                            ? renderTextWithSourceLinks(text, ragSources)
                            : text}
                        </MessageResponse>
                      );
                    }
                    default:
                      return null;
                  }
                })
              )}
              {message.role === "assistant" && ragSources.length > 0 && (
                <div className="mt-3">
                  <Sources>
                    <SourcesTrigger count={ragSources.length} />
                    <SourcesContent>
                      {ragSources.map((source, index) => (
                        <div key={source.id} className="space-y-1">
                          <Source
                            href={normalizeSourceUrl(source.url)}
                            title={source.title}
                          >
                            <span className="font-medium">
                              {index + 1}. {source.title}
                            </span>
                          </Source>
                          {source.description && (
                            <div className="text-muted-foreground text-xs">
                              {source.description}
                            </div>
                          )}
                        </div>
                      ))}
                    </SourcesContent>
                  </Sources>
                </div>
              )}
            </MessageContent>
            {/* {message.role === "assistant" && message.versions && ( */}
            {message.role === "assistant" && hasTextStarted && (
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
