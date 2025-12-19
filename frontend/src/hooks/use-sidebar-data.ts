import { useEffect, useMemo } from "react";
import { navToolGroups } from "@/config/navigation";
import { useAppStore } from "@/store/app-store";

/**
 * Loads sidebar data (authz, history) and derives visible tool groups.
 */
export const useSidebarData = () => {
  const authz = useAppStore((state) => state.authz);
  const fetchAuthz = useAppStore((state) => state.fetchAuthz);
  const history = useAppStore((state) => state.history);
  const fetchHistory = useAppStore((state) => state.fetchHistory);
  const activeToolIds = useAppStore((state) => state.activeToolIds);

  useEffect(() => {
    if (authz.status === "idle") {
      fetchAuthz();
    }
  }, [authz.status, fetchAuthz]);

  useEffect(() => {
    if (history.status === "idle") {
      fetchHistory();
    }
  }, [history.status, fetchHistory]);

  const visibleToolGroups = useMemo(
    () =>
      navToolGroups
        .filter((group) => authz.tools.includes(group.id))
        .map((group) => ({
          ...group,
          isActive: activeToolIds.includes(group.id) || group.isActive,
        })),
    [authz.tools, activeToolIds]
  );

  const user = {
    name: authz.user?.first_name
      ? `${authz.user.first_name} ${authz.user?.last_name ?? ""}`.trim()
      : authz.user?.email ?? "",
    email: authz.user?.email ?? "",
  };

  return {
    authz,
    history,
    visibleToolGroups,
    user,
  };
};