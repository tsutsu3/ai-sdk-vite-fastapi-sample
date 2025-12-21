import { useCallback, useEffect, useMemo, useState } from "react";
import { Archive, ArchiveRestore, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAppStore } from "@/store/app-store";
import type { ArchivedConversation } from "@/types/settings";
import { ConfirmDeleteDialog } from "@/components/app/dialog/confirm-delete-dialog";

type DataControlSettingsProps = {
  t: (key: string, params?: Record<string, unknown>) => string;
};

export function DataControlSettings({ t }: DataControlSettingsProps) {
  const [archivedOpen, setArchivedOpen] = useState(false);
  const [archiveAllOpen, setArchiveAllOpen] = useState(false);
  const [deleteAllOpen, setDeleteAllOpen] = useState(false);
  const [archivedChats, setArchivedChats] = useState<ArchivedConversation[]>([]);
  const [pendingDelete, setPendingDelete] =
    useState<ArchivedConversation | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const refreshHistory = useAppStore((state) => state.fetchHistory);

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
    fetch("/api/conversations?archived=true")
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        const conversations = Array.isArray(payload?.conversations)
          ? (payload.conversations as ArchivedConversation[])
          : [];
        setArchivedChats(conversations);
      })
      .catch(() => {})
      .finally(() => {
        setBusy(null);
      });
  }, [archivedOpen]);

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
        const response = await fetch(`/api/conversations/${conversationId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ archived: false }),
        });
        if (response.ok) {
          setArchivedChats((prev) =>
            prev.filter((item) => item.id !== conversationId)
          );
          refreshHistory(true);
        }
      } finally {
        setBusy(null);
      }
    },
    [refreshHistory]
  );

  const handleDelete = useCallback(
    async (conversationId: string) => {
      if (!conversationId) {
        return;
      }
      setBusy(`delete-${conversationId}`);
      try {
        const response = await fetch(`/api/conversations/${conversationId}`, {
          method: "DELETE",
        });
        if (response.ok) {
          setArchivedChats((prev) =>
            prev.filter((item) => item.id !== conversationId)
          );
          refreshHistory(true);
        }
      } finally {
        setBusy(null);
      }
    },
    [refreshHistory]
  );

  const handleArchiveAll = useCallback(async () => {
    setBusy("archive-all");
    try {
      const response = await fetch("/api/conversations/archive-all", {
        method: "PATCH",
      });
      if (response.ok) {
        refreshHistory(true, false);
      }
    } finally {
      setBusy(null);
    }
  }, [refreshHistory]);

  const handleDeleteAll = useCallback(async () => {
    setBusy("delete-all");
    try {
      const response = await fetch("/api/conversations", {
        method: "DELETE",
      });
      if (response.ok) {
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
    [archivedChats, formatDate]
  );

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium">{t("archivedChats")}</p>
            <p className="text-xs text-muted-foreground">
              {t("archivedChatsDescription")}
            </p>
          </div>
          <Button onClick={() => setArchivedOpen(true)} variant="outline">
            {t("manage")}
          </Button>
        </div>
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium">{t("archiveAllChats")}</p>
            <p className="text-xs text-muted-foreground">
              {t("archiveAllChatsDescription")}
            </p>
          </div>
          <Button onClick={() => setArchiveAllOpen(true)} variant="outline">
            {t("archiveAll")}
          </Button>
        </div>
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium">{t("deleteAllChats")}</p>
            <p className="text-xs text-muted-foreground">
              {t("deleteAllChatsDescription")}
            </p>
          </div>
          <Button onClick={() => setDeleteAllOpen(true)} variant="destructive">
            {t("deleteAll")}
          </Button>
        </div>
      </div>

      <Dialog open={archivedOpen} onOpenChange={setArchivedOpen}>
        <DialogContent className="max-w-3xl">
          <DialogTitle>{t("archivedChats")}</DialogTitle>
          <div className="max-h-[60vh] overflow-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-background">
                <tr className="text-left text-muted-foreground">
                  <th className="py-2 pr-4">{t("title")}</th>
                  <th className="py-2 pr-4">{t("created")}</th>
                  <th className="py-2 text-right">{t("actions")}</th>
                </tr>
              </thead>
              <tbody>
                {archivedRows.length === 0 && (
                  <tr>
                    <td
                      className="py-6 text-center text-muted-foreground"
                      colSpan={3}
                    >
                      {t("noArchivedChats")}
                    </td>
                  </tr>
                )}
                {archivedRows.map((chat) => (
                  <tr key={chat.id} className="border-t">
                    <td className="py-2 pr-4">
                      {chat.title || "Conversation"}
                    </td>
                    <td className="py-2 pr-4">{chat.createdAtDisplay}</td>
                    <td className="py-2 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => handleUnarchive(chat.id)}
                          disabled={busy === `unarchive-${chat.id}`}
                        >
                          <ArchiveRestore className="size-4" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => setPendingDelete(chat)}
                          disabled={busy === `delete-${chat.id}`}
                        >
                          <Trash2 className="size-4 text-destructive" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DialogContent>
      </Dialog>

      <ConfirmDeleteDialog
        open={Boolean(pendingDelete)}
        onOpenChange={() => setPendingDelete(null)}
        title={t("delete")}
        description={t("confirmDelete", { title: pendingDelete?.title ?? "" })}
        confirmLabel={t("delete")}
        cancelLabel={t("cancel")}
        onConfirm={async () => {
          if (pendingDelete) {
            await handleDelete(pendingDelete.id);
          }
          setPendingDelete(null);
        }}
      />

      <Dialog open={archiveAllOpen} onOpenChange={setArchiveAllOpen}>
        <DialogContent>
          <DialogTitle>{t("archiveAllChats")}</DialogTitle>
          <p className="text-sm text-muted-foreground">
            {t("archiveAllConfirm")}
          </p>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="ghost" onClick={() => setArchiveAllOpen(false)}>
              {t("cancel")}
            </Button>
            <Button
              onClick={async () => {
                await handleArchiveAll();
                setArchiveAllOpen(false);
              }}
            >
              <Archive className="mr-2 size-4" />
              {t("archiveAll")}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={deleteAllOpen} onOpenChange={setDeleteAllOpen}>
        <DialogContent>
          <DialogTitle>{t("deleteAllChats")}</DialogTitle>
          <p className="text-sm text-muted-foreground">
            {t("deleteAllConfirm")}
          </p>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="ghost" onClick={() => setDeleteAllOpen(false)}>
              {t("cancel")}
            </Button>
            <Button
              variant="destructive"
              onClick={async () => {
                await handleDeleteAll();
                setDeleteAllOpen(false);
              }}
            >
              <Trash2 className="mr-2 size-4" />
              {t("deleteAll")}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
