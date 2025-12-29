import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  ChainOfThought,
  ChainOfThoughtContent,
  ChainOfThoughtHeader,
  ChainOfThoughtStep,
} from "@/components/ai-elements/chain-of-thought";
import {
  Source,
  Sources,
  SourcesContent,
  SourcesTrigger,
} from "@/components/ai-elements/sources";
import { Loader } from "@/components/ai-elements/loader";
import type { ToolsViewModel } from "@/features/tools/hooks/tools-view-model-types";
import { ChatMessageList } from "@/features/chat/components/chat-message-list";
import { ToolsPromptInput } from "@/features/tools/components/tools-prompt-input";
import { useEffect, useRef } from "react";
import type { StickToBottomContext } from "use-stick-to-bottom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export type ToolsViewProps = {
  viewModel: ToolsViewModel;
};

export const ToolsView = ({ viewModel }: ToolsViewProps) => {
  const { scroll, messageList, prompt, status, chainOfThought, sources, emptyState } =
    viewModel;

  const scrollContextRef = useRef<StickToBottomContext | null>(null);
  const topSentinelRef = useRef<HTMLDivElement | null>(null);
  const isEmpty = messageList.messages.length === 0;

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
            {chainOfThought.steps.length > 0 && (
              <ChainOfThought
                open={chainOfThought.open}
                onOpenChange={chainOfThought.onOpenChange}
              >
                <ChainOfThoughtHeader>RAG Progress</ChainOfThoughtHeader>
                <ChainOfThoughtContent>
                  {chainOfThought.steps.map((step) => (
                    <ChainOfThoughtStep
                      key={step.id}
                      label={step.label}
                      description={step.description}
                      status={step.status}
                    />
                  ))}
                </ChainOfThoughtContent>
              </ChainOfThought>
            )}
            {sources.items.length > 0 && (
              <Sources>
                <SourcesTrigger count={sources.items.length} />
                <SourcesContent>
                  {sources.items.map((source) => (
                    <Source
                      href={source.url}
                      key={source.id}
                      title={source.title}
                    />
                  ))}
                </SourcesContent>
              </Sources>
            )}
            <ChatMessageList viewModel={messageList} />
            <div className="min-h-6">
              {status === "submitted" && <Loader />}
            </div>
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>
        <ToolsPromptInput viewModel={prompt} />
      </div>
    </div>
  );
};
