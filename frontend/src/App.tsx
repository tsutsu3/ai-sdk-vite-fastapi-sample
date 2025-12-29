import { RouterProvider } from "react-router";
import { router } from "@/app/router";
import { ThemeProvider } from "@/app/providers/theme-provider";

export default function App() {
  return (
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}
