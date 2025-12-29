import { Archive, ArchiveRestore, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { ConfirmDeleteDialog } from "@/components/app/dialog/confirm-delete-dialog";
import type { ArchivedConversation } from "@/features/settings/types/settings";

export type DataControlSettingsViewModel = {
  t: (key: string, params?: Record<string, unknown>) => string;
  archivedOpen: boolean;
  archiveAllOpen: boolean;
  deleteAllOpen: boolean;
  archivedRows: Array<ArchivedConversation & { createdAtDisplay: string }>;
  pendingDelete: ArchivedConversation | null;
  busy: string | null;
  setArchivedOpen: (open: boolean) => void;
  setArchiveAllOpen: (open: boolean) => void;
  setDeleteAllOpen: (open: boolean) => void;
  setPendingDelete: (chat: ArchivedConversation | null) => void;
  handleUnarchive: (conversationId: string) => Promise<void>;
  handleDelete: (conversationId: string) => Promise<void>;
  handleArchiveAll: () => Promise<void>;
  handleDeleteAll: () => Promise<void>;
};

export type DataControlSettingsViewProps = {
  viewModel: DataControlSettingsViewModel;
};

export const DataControlSettingsView = ({
  viewModel,
}: DataControlSettingsViewProps) => {
  const {
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
  } = viewModel;

  return (
    <div className="space-y-6">
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium">{t("archivedChats")}</p>
          <p className="text-muted-foreground text-xs">
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
          <p className="text-muted-foreground text-xs">
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
          <p className="text-muted-foreground text-xs">
            {t("deleteAllChatsDescription")}
          </p>
        </div>
        <Button onClick={() => setDeleteAllOpen(true)} variant="destructive">
          {t("deleteAll")}
        </Button>
      </div>
    </div>

    {/* Manage archived chats dialog */}
    <Dialog open={archivedOpen} onOpenChange={setArchivedOpen}>
      <DialogContent className="w-full max-w-4xl! px-0">
        <DialogTitle className="px-6">{t("archivedChats")}</DialogTitle>
        <div className="max-h-[60vh] overflow-auto px-6">
          <table className="w-full text-sm">
            <thead className="bg-background sticky top-0">
              <tr className="text-muted-foreground text-left">
                <th className="py-2 pr-4">{t("title")}</th>
                <th className="py-2 pr-4">{t("created")}</th>
                <th className="py-2 text-right">{t("actions")}</th>
              </tr>
            </thead>
            <tbody>
              {archivedRows.length === 0 && (
                <tr>
                  <td
                    className="text-muted-foreground py-6 text-center"
                    colSpan={3}
                  >
                    {t("noArchivedChats")}
                  </td>
                </tr>
              )}
              {archivedRows.map((chat) => (
                <tr key={chat.id} className="border-t">
                  <td className="py-2 pr-4">{chat.title || "Conversation"}</td>
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
                        <Trash2 className="text-destructive size-4" />
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

    {/* Delete confirmation dialog within the 'Manage archived chats dialog' */}
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

    {/* Archive all chats dialog */}
    <Dialog open={archiveAllOpen} onOpenChange={setArchiveAllOpen}>
      <DialogContent>
        <DialogTitle>{t("archiveAllChats")}</DialogTitle>
        <p className="text-muted-foreground text-sm">
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

    {/* Delete all chats dialog */}
    <Dialog open={deleteAllOpen} onOpenChange={setDeleteAllOpen}>
      <DialogContent>
        <DialogTitle>{t("deleteAllChats")}</DialogTitle>
        <p className="text-muted-foreground text-sm">{t("deleteAllConfirm")}</p>
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
};
