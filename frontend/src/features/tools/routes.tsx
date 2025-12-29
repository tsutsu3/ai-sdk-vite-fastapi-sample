import ToolsPage from "@/features/tools/pages/tools-page";

export const toolRoutes = [
  {
    path: "/tools/:type",
    element: <ToolsPage />,
    handle: {
      breadcrumb: (params: { type: string }) => `Tools / ${params.type}`,
    },
  },
];
