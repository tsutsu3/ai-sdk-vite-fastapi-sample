import NotFoundPage from "@/features/error/pages/not-found-page";

export const errorRoutes = [
  {
    path: "*",
    element: <NotFoundPage />,
    handle: { breadcrumb: "Not Found" },
  },
];
