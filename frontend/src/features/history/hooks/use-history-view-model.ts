import { useCallback, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import type { HistoryItem } from "@/shared/types/history";
import { useAppStore } from "@/store/app-store";
import {
  deleteConversation,
  updateConversation,
} from "@/services/api/conversations";

export const useHistoryViewModel = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const removeHistoryItem = useAppStore((state) => state.removeHistoryItem);
  const upsertHistoryItem = useAppStore((state) => state.upsertHistoryItem);
  const [pendingDelete, setPendingDelete] = useState<HistoryItem | null>(null);
  const [pendingRename, setPendingRename] = useState<HistoryItem | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const extractConversationId = (url: string) => {
    const parts = url.split("/chat/c/");
    if (parts.length > 1) {
      return parts[1];
    }
    const toolParts = url.split("/c/");
    return toolParts.length > 1 ? toolParts[1] : "";
  };

  const activeConversationId = useMemo(() => {
    const path = location.pathname;
    if (path.includes("/chat/c/")) {
      return path.split("/chat/c/")[1] ?? "";
    }
    if (path.includes("/tools/") && path.includes("/c/")) {
      return path.split("/c/")[1] ?? "";
    }
    return "";
  }, [location.pathname]);

  const isActiveConversation = useCallback(
    (url: string) => {
      const conversationId = extractConversationId(url);
      return Boolean(conversationId) && conversationId === activeConversationId;
    },
    [activeConversationId],
  );

  const handleArchive = async (item: HistoryItem) => {
    const conversationId = extractConversationId(item.url);
    if (!conversationId) {
      return;
    }
    try {
      const updated = await updateConversation(conversationId, {
        archived: true,
      });
      if (!updated) {
        return;
      }
      removeHistoryItem(item.url);
      if (activeConversationId === conversationId) {
        navigate("/chat");
      }
    } catch {
      return;
    }
  };

  const handleDelete = async (item: HistoryItem) => {
    const conversationId = extractConversationId(item.url);
    if (!conversationId) {
      return;
    }
    try {
      const ok = await deleteConversation(conversationId);
      if (!ok) {
        return;
      }
      removeHistoryItem(item.url);
      if (activeConversationId === conversationId) {
        navigate("/chat");
      }
    } catch {
      return;
    }
  };

  const handleRename = async (item: HistoryItem, nextTitle: string) => {
    const conversationId = extractConversationId(item.url);
    if (!conversationId || !nextTitle.trim()) {
      return;
    }
    try {
      const updated = await updateConversation(conversationId, {
        title: nextTitle.trim(),
      });
      if (!updated) {
        return;
      }
      const updatedAt = updated.updatedAt ?? item.updatedAt;
      upsertHistoryItem({
        name: nextTitle.trim(),
        url: item.url,
        updatedAt,
      });
    } catch {
      return;
    }
  };

  const formatUpdatedAt = (value: string) => {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(parsed);
  };

  return {
    pendingDelete,
    pendingRename,
    renameValue,
    setPendingDelete,
    setPendingRename,
    setRenameValue,
    handleArchive,
    handleDelete,
    handleRename,
    formatUpdatedAt,
    isActiveConversation,
  };
};
