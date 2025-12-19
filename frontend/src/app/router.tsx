import { createBrowserRouter } from "react-router";

import AppLayout from "./layout/AppLayout";

import ChatPage from "@/routes/chat/ChatPage";
import RagPage from "@/routes/rag/RagPage";
import NotFoundPage from "@/routes/error/NotFoundPage";
import HomePage from "@/routes/home/HomePage";

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      {
        path: "/",
        element: <HomePage />,
        handle: { breadcrumb: "Home" },
      },
      {
        path: "/chat",
        element: <ChatPage />,
        handle: { breadcrumb: "Chat" },
      },
      {
        path: "/tools/:type",
        element: <RagPage />,
        handle: {
          breadcrumb: (params: { type: string }) => `Tools / ${params.type}`,
        },
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
      {
        path: "*",
        element: <NotFoundPage />,
        handle: { breadcrumb: "Not Found" },
      },
    ],
  },
]);
