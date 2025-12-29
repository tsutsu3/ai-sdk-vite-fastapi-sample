import HomePage from "@/features/home/pages/home-page";

export const homeRoutes = [
  {
    path: "/",
    element: <HomePage />,
    handle: { breadcrumb: "Home" },
  },
];
