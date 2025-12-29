import { useEffect, useMemo } from "react";
import { useLocation } from "react-router";
import { useAppStore } from "@/store/app-store";
import { useSidebarViewModel } from "@/features/navigation/hooks/use-sidebar-view-model";

export const useAppLayoutViewModel = () => {
  const location = useLocation();
  const capabilities = useAppStore((state) => state.capabilities);
  const fetchCapabilities = useAppStore((state) => state.fetchCapabilities);
  const sidebar = useSidebarViewModel();

  const breadcrumbs = useMemo(() => {
    const segments = location.pathname.split("/").filter(Boolean);
    return ["Home", ...segments];
  }, [location.pathname]);

  useEffect(() => {
    if (capabilities.status === "idle") {
      fetchCapabilities();
    }
  }, [capabilities.status, fetchCapabilities]);

  return {
    breadcrumbs,
    sidebar,
  };
};
