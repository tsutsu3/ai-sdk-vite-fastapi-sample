import { ChatView } from "@/components/app/chat/ChatView";
import { useChatController } from "@/hooks/use-chat-controller";

const ChatPage = () => {
  const controller = useChatController();

  return <ChatView {...controller} />;
};

export default ChatPage;
