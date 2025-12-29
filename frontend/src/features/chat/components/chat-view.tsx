import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import type { ChatViewModel } from "@/features/chat/hooks/use-chat-view-model";
import { useEffect, useRef } from "react";
import type { StickToBottomContext } from "use-stick-to-bottom";
import { ChatMessageList } from "./chat-message-list";
import { ChatPromptInput } from "./chat-prompt-input";
import { Loader } from "@/components/ai-elements/loader";
import { useTranslation } from "react-i18next";

/**
 * Props for the presentational chat view.
 */
export type ChatViewProps = {
  viewModel: ChatViewModel;
};

/**
 * Pure UI view for the chat page. Handles rendering and event forwarding only.
 */
export const ChatView = ({ viewModel }: ChatViewProps) => {
  const { scroll, messageList, prompt, status } = viewModel;
  const { t } = useTranslation();
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
                <h2 className="text-2xl font-semibold">
                  {t("chatEmptyTitle")}
                </h2>
                <p className="text-muted-foreground text-sm">
                  {t("chatEmptySubtitle")}
                </p>
              </div>
              <ChatPromptInput viewModel={prompt} />
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
          <ConversationContent className="mx-auto w-full max-w-4xl px-6 pb-12">
            <div ref={topSentinelRef} className="h-1" />
            <ChatMessageList viewModel={messageList} />
            <div className="min-h-6">
              {status === "submitted" && <Loader />}
            </div>
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>
        <ChatPromptInput viewModel={prompt} />
      </div>
    </div>
  );
};
