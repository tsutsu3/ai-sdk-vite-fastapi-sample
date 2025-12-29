import { useEffect, useMemo, useRef, useState } from "react";
import { SquareTerminal } from "lucide-react";

import { toolGroupIcons } from "@/features/navigation/config/tool-icons";
import { navLinkGroups, navMainItems } from "@/features/navigation/config/navigation";
import { useAppStore } from "@/store/app-store";
import type { NavToolGroup } from "@/shared/types/ui";
import type { AppSidebarViewModel } from "@/components/app/sidebar/app-sidebar";
import { useHistoryViewModel } from "@/features/history/hooks/use-history-view-model";
import { useSettingsDialogViewModel } from "@/features/settings/hooks/use-settings-dialog-view-model";
import { useBillingDialogViewModel } from "@/features/billing/hooks/use-billing-dialog-view-model";
import { useTranslation } from "react-i18next";
import { useSidebar } from "@/components/ui/sidebar";

/**
 * ViewModel for the application sidebar.
 */
export const useSidebarViewModel = (): AppSidebarViewModel => {
  const authz = useAppStore((state) => state.authz);
  const fetchAuthz = useAppStore((state) => state.fetchAuthz);
  const history = useAppStore((state) => state.history);
  const fetchHistory = useAppStore((state) => state.fetchHistory);
  const fetchMoreHistory = useAppStore((state) => state.fetchMoreHistory);
  const activeToolIds = useAppStore((state) => state.activeToolIds);
  const addActiveToolId = useAppStore((state) => state.addActiveToolId);
  const removeActiveToolId = useAppStore((state) => state.removeActiveToolId);
  const historyViewModel = useHistoryViewModel();
  const settingsDialog = useSettingsDialogViewModel();
  const billingDialog = useBillingDialogViewModel();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [billingOpen, setBillingOpen] = useState(false);
  const { t } = useTranslation();
  const { isMobile } = useSidebar();
  const historyScrollRef = useRef<HTMLDivElement | null>(null);
  const historySentinelRef = useRef<HTMLLIElement | null>(null);

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

  useEffect(() => {
    const scrollElement = historyScrollRef.current;
    const sentinel = historySentinelRef.current;
    if (!scrollElement || !sentinel || !history.continuationToken || history.loadingMore) {
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          fetchMoreHistory();
        }
      },
      {
        root: scrollElement,
        rootMargin: "120px 0px 120px 0px",
        threshold: 0,
      },
    );
    observer.observe(sentinel);
    return () => {
      observer.disconnect();
    };
  }, [fetchMoreHistory, history.continuationToken, history.loadingMore]);

  const visibleToolGroups = useMemo(() => {
    const allowed = authz.tools.length
      ? authz.toolGroups.filter((group) => authz.tools.includes(group.id))
      : authz.toolGroups;
    return allowed.map<NavToolGroup>((group) => ({
      id: group.id,
      url: "#",
      icon: toolGroupIcons[group.id] ?? SquareTerminal,
      isActive: activeToolIds.includes(group.id),
      items: group.items?.map((item) => ({
        id: item.id,
        url: `/tools/${item.id}`,
      })),
    }));
  }, [authz.tools, authz.toolGroups, activeToolIds]);

  const user = {
    name: authz.user?.first_name
      ? `${authz.user.first_name} ${authz.user?.last_name ?? ""}`.trim()
      : (authz.user?.email ?? ""),
    email: authz.user?.email ?? "",
  };

  const historyItems = useMemo(
    () =>
      history.items.map((item) => ({
        ...item,
        isActive: historyViewModel.isActiveConversation(item.url),
      })),
    [history.items, historyViewModel],
  );

  const labels = {
    tools: t("tools"),
    history: t("history"),
    links: t("links"),
  };

  return {
    mainMenu: {
      items: navMainItems,
      t,
    },
    toolMenu: {
      label: labels.tools,
      items: visibleToolGroups,
      isLoading: authz.status === "loading",
      openGroupIds: activeToolIds,
      onToggleGroup: (groupId, open) => {
        if (open) {
          addActiveToolId(groupId);
        } else {
          removeActiveToolId(groupId);
        }
      },
      t,
    },
    historyMenu: {
      label: labels.history,
      items: historyItems,
      scrollRef: historyScrollRef,
      sentinelRef: historySentinelRef,
      isMobile,
      t,
      pendingDelete: historyViewModel.pendingDelete,
      pendingRename: historyViewModel.pendingRename,
      renameValue: historyViewModel.renameValue,
      setPendingDelete: historyViewModel.setPendingDelete,
      setPendingRename: historyViewModel.setPendingRename,
      setRenameValue: historyViewModel.setRenameValue,
      handleArchive: historyViewModel.handleArchive,
      handleDelete: historyViewModel.handleDelete,
      handleRename: historyViewModel.handleRename,
      formatUpdatedAt: historyViewModel.formatUpdatedAt,
    },
    linkMenu: {
      label: labels.links,
      items: navLinkGroups,
      className: "mt-auto",
      openGroupIds: activeToolIds,
      onToggleGroup: (groupId, open) => {
        if (open) {
          addActiveToolId(groupId);
        } else {
          removeActiveToolId(groupId);
        }
      },
      t,
    },
    userMenu: {
      user,
      avatarName: user.name || user.email || undefined,
      authzStatus: authz.status,
      settingsOpen,
      onSettingsOpenChange: setSettingsOpen,
      billingOpen,
      onBillingOpenChange: setBillingOpen,
      settingsDialog,
      billingDialog,
      isMobile,
      t,
    },
  };
};
