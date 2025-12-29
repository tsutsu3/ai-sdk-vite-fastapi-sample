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

export type ToolsViewProps = {
  viewModel: ToolsViewModel;
};

export const ToolsView = ({ viewModel }: ToolsViewProps) => {
  const { scroll, messageList, prompt, status, chainOfThought, sources } =
    viewModel;

  const scrollContextRef = useRef<StickToBottomContext | null>(null);
  const topSentinelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scroll.setScrollContextRef(scrollContextRef.current);
  }, [scroll]);

  useEffect(() => {
    scroll.setTopSentinelRef(topSentinelRef.current);
  }, [scroll]);

  return (
    <div className="relative size-full h-full min-h-0">
      <div className="flex h-full min-h-0 flex-col overflow-hidden">
        <Conversation
          className="min-h-0 flex-1 overflow-y-hidden"
          contextRef={scrollContextRef}
        >
          <ConversationContent className="mx-auto w-full max-w-4xl space-y-6 px-6 pb-12">
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
