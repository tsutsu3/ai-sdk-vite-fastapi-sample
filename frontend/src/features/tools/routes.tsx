import ToolsPage from "@/features/tools/pages/tools-page";

export const toolRoutes = [
  {
    path: "/tools/:type",
    element: <ToolsPage />,
    handle: {
      breadcrumb: (params: { type: string }) => `Tools / ${params.type}`,
    },
  },
  {
    path: "/tools/:type/c/:id",
    element: <ToolsPage />,
    handle: {
      breadcrumb: (params: { type: string; id: string }) =>
        `Tools / ${params.type} / ${params.id}`,
    },
  },
  {
    path: "/tools/c/:id",
    element: <ToolsPage />,
    handle: {
      breadcrumb: (params: { id: string }) => `Tools / ${params.id}`,
    },
  },
];
