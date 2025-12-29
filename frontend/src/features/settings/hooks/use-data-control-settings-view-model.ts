import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { ArchivedConversation } from "@/features/settings/types/settings";
import { useAppStore } from "@/store/app-store";
import {
  deleteAllConversations,
  deleteConversation,
  fetchConversations,
  updateAllConversations,
  updateConversation,
} from "@/services/api/conversations";

export const useDataControlSettingsViewModel = () => {
  const { t } = useTranslation();
  const [archivedOpen, setArchivedOpen] = useState(false);
  const [archiveAllOpen, setArchiveAllOpen] = useState(false);
  const [deleteAllOpen, setDeleteAllOpen] = useState(false);
  const [archivedChats, setArchivedChats] = useState<ArchivedConversation[]>(
    [],
  );
  const [pendingDelete, setPendingDelete] =
    useState<ArchivedConversation | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const refreshHistory = useAppStore((state) => state.fetchHistory);
  const conversationsPageSizeMax = useAppStore(
    (state) => state.capabilities.apiPageSizes.conversationsPageSizeMax,
  );

  const formatDate = useCallback((value?: string | null) => {
    if (!value) {
      return "-";
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(parsed);
  }, []);

  const loadArchived = useCallback(() => {
    if (!archivedOpen) {
      return;
    }
    setBusy("archived");
    fetchConversations({
      archived: true,
      limit:
        typeof conversationsPageSizeMax === "number" && conversationsPageSizeMax > 0
          ? conversationsPageSizeMax
          : 200,
    })
      .then((result) => {
        setArchivedChats(result.conversations as ArchivedConversation[]);
      })
      .catch(() => {})
      .finally(() => {
        setBusy(null);
      });
  }, [archivedOpen, conversationsPageSizeMax]);

  useEffect(() => {
    loadArchived();
  }, [loadArchived]);

  const handleUnarchive = useCallback(
    async (conversationId: string) => {
      if (!conversationId) {
        return;
      }
      setBusy(`unarchive-${conversationId}`);
      try {
        const updated = await updateConversation(conversationId, {
          archived: false,
        });
        if (updated) {
          setArchivedChats((prev) =>
            prev.filter((item) => item.id !== conversationId),
          );
          refreshHistory(true);
        }
      } finally {
        setBusy(null);
      }
    },
    [refreshHistory],
  );

  const handleDelete = useCallback(
    async (conversationId: string) => {
      if (!conversationId) {
        return;
      }
      setBusy(`delete-${conversationId}`);
      try {
        const ok = await deleteConversation(conversationId);
        if (ok) {
          setArchivedChats((prev) =>
            prev.filter((item) => item.id !== conversationId),
          );
          refreshHistory(true);
        }
      } finally {
        setBusy(null);
      }
    },
    [refreshHistory],
  );

  const handleArchiveAll = useCallback(async () => {
    setBusy("archive-all");
    try {
      const ok = await updateAllConversations({ archived: true });
      if (ok) {
        refreshHistory(true, false);
      }
    } finally {
      setBusy(null);
    }
  }, [refreshHistory]);

  const handleDeleteAll = useCallback(async () => {
    setBusy("delete-all");
    try {
      const ok = await deleteAllConversations();
      if (ok) {
        refreshHistory(true, false);
      }
    } finally {
      setBusy(null);
    }
  }, [refreshHistory]);

  const archivedRows = useMemo(
    () =>
      archivedChats.map((chat) => ({
        ...chat,
        createdAtDisplay: formatDate(chat.createdAt || chat.updatedAt),
      })),
    [archivedChats, formatDate],
  );

  return {
    t,
    archivedOpen,
    archiveAllOpen,
    deleteAllOpen,
    archivedRows,
    pendingDelete,
    busy,
    setArchivedOpen,
    setArchiveAllOpen,
    setDeleteAllOpen,
    setPendingDelete,
    handleUnarchive,
    handleDelete,
    handleArchiveAll,
    handleDeleteAll,
  };
};
