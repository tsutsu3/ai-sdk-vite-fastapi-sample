import ChatPage from "@/features/chat/pages/chat-page";

export const chatRoutes = [
  {
    path: "/chat",
    element: <ChatPage />,
    handle: { breadcrumb: "Chat" },
  },
  {
    path: "/chat/c/:id",
    element: <ChatPage />,
    handle: {
      breadcrumb: (params: { id: string }) => `Chat / ${params.id}`,
    },
  },
  {
    path: "/tools/:type/c/:id",
    element: <ChatPage />,
    handle: {
      breadcrumb: (params: { type: string; id: string }) =>
        `Tools / ${params.type} / ${params.id}`,
    },
  },
];
