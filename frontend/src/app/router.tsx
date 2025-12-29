import { createBrowserRouter } from "react-router";

import { AppLayout } from "./layout/app-layout";

import { chatRoutes } from "@/features/chat/routes";
import { toolRoutes } from "@/features/tools/routes";
import { homeRoutes } from "@/features/home/routes";
import { errorRoutes } from "@/features/error/routes";

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [...homeRoutes, ...chatRoutes, ...toolRoutes, ...errorRoutes],
  },
]);
