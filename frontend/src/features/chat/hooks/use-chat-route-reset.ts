import { useEffect, useRef } from "react";
import { useLocation } from "react-router";
import type { UIMessage } from "ai";

type UseChatRouteResetArgs = {
  setMessages: (messages: UIMessage[] | ((prev: UIMessage[]) => UIMessage[])) => void;
  resetConversation: () => void;
};

/**
 *  Reset chat state only when returning from an existing conversation to `/chat`.
 *  After sending a message, the app briefly renders `/chat` before navigating to
 *  `/chat/c/:id`. Resetting on every `/chat` render would cause messages to flicker,
 *  so we check the previous pathname to reset only on an explicit "new chat" action.
 */
export const useChatRouteReset = ({
  setMessages,
  resetConversation,
}: UseChatRouteResetArgs) => {
  const location = useLocation();
  const prevPathnameRef = useRef<string | null>(null);

  useEffect(() => {
    const prev = prevPathnameRef.current;
    const current = location.pathname;

    if (current === "/chat" && prev?.startsWith("/chat/c/")) {
      // Only reset when explicitly starting a new chat to avoid flicker during redirect.
      setMessages([]);
      resetConversation();
    }

    prevPathnameRef.current = current;
  }, [location.pathname, setMessages, resetConversation]);
};
