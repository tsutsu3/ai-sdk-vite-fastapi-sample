import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import { Loader } from "@/components/ai-elements/loader";
import type { ToolsViewModel } from "@/features/tools/hooks/tools-view-model-types";
import { ChatMessageList } from "@/components/app/chat/chat-message-list";
import { ToolsPromptInput } from "@/features/tools/components/tools-prompt-input";
import { useEffect, useRef } from "react";
import type { StickToBottomContext } from "use-stick-to-bottom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export type ToolsViewProps = {
  viewModel: ToolsViewModel;
};

export const ToolsView = ({ viewModel }: ToolsViewProps) => {
  const { scroll, messageList, prompt, status, emptyState } = viewModel;

  const scrollContextRef = useRef<StickToBottomContext | null>(null);
  const topSentinelRef = useRef<HTMLDivElement | null>(null);
  const isEmpty = messageList.messages.length === 0;
  const lastAssistantMessage = [...messageList.messages]
    .reverse()
    .find((message) => message.role === "assistant");
  const lastAssistantTextStarted = Boolean(
    lastAssistantMessage?.parts.some((part) => part.type === "text"),
  );
  const shouldShowLoader =
    status === "submitted" ||
    (status === "streaming" &&
      lastAssistantMessage &&
      !lastAssistantTextStarted);

  useEffect(() => {
    scroll.setScrollContextRef(scrollContextRef.current);
  }, [scroll]);

  useEffect(() => {
    scroll.setTopSentinelRef(topSentinelRef.current);
  }, [scroll]);

  if (isEmpty) {
    return (
      <div className="relative size-full h-full min-h-0">
        <div className="flex h-full min-h-0 flex-col overflow-hidden">
          <div className="flex flex-1 items-center justify-center px-6">
            <div className="w-full max-w-3xl space-y-6">
              <div className="space-y-2 text-center">
                <h2 className="text-2xl font-semibold">{emptyState.title}</h2>
                <p className="text-muted-foreground text-sm">
                  {emptyState.subtitle}
                </p>
              </div>
              <div className="grid gap-3 px-3 md:grid-cols-3">
                {emptyState.samples.map((sample, index) => (
                  <Button
                    key={`${sample}-${index}`}
                    className={cn(
                      "bg-background text-card-foreground flex min-h-26 w-full items-start rounded-xl border p-4 text-left text-sm font-normal whitespace-normal transition-all",
                      "hover:border-foreground/10 hover:bg-muted/30 hover:-translate-y-0.5 hover:shadow-md",
                    )}
                    onClick={() => {
                      prompt.onTextChange(sample);
                      prompt.textareaRef.current?.focus();
                    }}
                  >
                    {sample}
                  </Button>
                ))}
              </div>
              <ToolsPromptInput
                viewModel={prompt}
                className="static max-w-3xl pb-0"
              />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative size-full h-full min-h-0">
      <div className="flex h-full min-h-0 flex-col overflow-hidden">
        <Conversation
          className="min-h-0 flex-1 overflow-y-hidden"
          contextRef={scrollContextRef}
        >
          <ConversationContent className="mx-auto w-full max-w-3xl space-y-6 px-6 pb-12">
            <div ref={topSentinelRef} className="h-1" />
            <ChatMessageList viewModel={messageList} />
            <div className="min-h-6">{shouldShowLoader && <Loader />}</div>
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>
        <ToolsPromptInput viewModel={prompt} />
      </div>
    </div>
  );
};
