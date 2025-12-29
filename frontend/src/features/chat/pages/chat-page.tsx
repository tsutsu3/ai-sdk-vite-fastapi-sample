import { ChatView } from "@/features/chat/components/chat-view";
import { useChatViewModel } from "@/features/chat/hooks/use-chat-view-model";

const ChatPage = () => {
  const viewModel = useChatViewModel();

  return <ChatView viewModel={viewModel} />;
};

export default ChatPage;
