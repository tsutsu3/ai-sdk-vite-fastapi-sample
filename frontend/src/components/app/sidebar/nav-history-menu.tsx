"use client";

import { Archive, MoreHorizontal, Pencil, Trash2 } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Link, useLocation, useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import type { HistoryItem } from "@/types/history";
import { useAppStore } from "@/store/app-store";
import { useState } from "react";
import { Separator } from "@radix-ui/react-separator";
import { ConfirmDeleteDialog } from "@/components/app/dialog/confirm-delete-dialog";

export function NavHistoryMenu({
  label,
  items,
}: {
  label?: string;
  items: HistoryItem[];
}) {
  const { isMobile } = useSidebar();
  const { t } = useTranslation();
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

  const extractActiveConversationId = () => {
    const path = location.pathname;
    if (path.includes("/chat/c/")) {
      return path.split("/chat/c/")[1] ?? "";
    }
    if (path.includes("/tools/") && path.includes("/c/")) {
      return path.split("/c/")[1] ?? "";
    }
    return "";
  };

  const activeConversationId = extractActiveConversationId();

  const handleArchive = async (item: HistoryItem) => {
    const conversationId = extractConversationId(item.url);
    if (!conversationId) {
      return;
    }
    try {
      const response = await fetch(`/api/conversations/${conversationId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ archived: true }),
      });
      if (!response.ok) {
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
      const response = await fetch(`/api/conversations/${conversationId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
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
      const response = await fetch(`/api/conversations/${conversationId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: nextTitle.trim() }),
      });
      if (!response.ok) {
        return;
      }
      const payload = await response.json().catch(() => null);
      const updatedAt = payload?.updatedAt ?? item.updatedAt;
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

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden flex flex-col min-h-0 ">
      {label && <SidebarGroupLabel>{label}</SidebarGroupLabel>}

      <div className="flex-1 overflow-y-auto">
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.url}>
              <Tooltip delayDuration={500}>
                <TooltipTrigger asChild>
                  <SidebarMenuButton asChild>
                    <Link to={item.url} className="flex-1">
                      <span>{item.name}</span>
                    </Link>
                  </SidebarMenuButton>
                </TooltipTrigger>
                <TooltipContent>
                  <div className="flex flex-col gap-1 max-w-[40em]">
                    <span className="wrap-break-word">{item.name}</span>
                    <span>
                      {t("updated")}: {formatUpdatedAt(item.updatedAt)}
                    </span>
                  </div>
                </TooltipContent>
              </Tooltip>
              {/* Dropdown menu for additional actions */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuAction showOnHover>
                    <MoreHorizontal />
                    <span className="sr-only">More</span>
                  </SidebarMenuAction>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  className="w-48"
                  side={isMobile ? "bottom" : "right"}
                  align={isMobile ? "end" : "start"}
                >
                  <DropdownMenuItem
                    onSelect={() => {
                      setPendingRename(item);
                      setRenameValue(item.name);
                    }}
                  >
                    <Pencil className="text-muted-foreground" />
                    <span>{t("rename")}</span>
                  </DropdownMenuItem>
                  <Separator className="my-1 h-px bg-sidebar-border" />
                  <DropdownMenuItem onSelect={() => handleArchive(item)}>
                    <Archive className="text-muted-foreground" />
                    <span>{t("archive")}</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem onSelect={() => setPendingDelete(item)}>
                    <Trash2 className="text-destructive" />
                    <span className="text-destructive">{t("delete")}</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </div>
      {/* Delete confirmation dialog */}
      <ConfirmDeleteDialog
        open={Boolean(pendingDelete)}
        onOpenChange={() => setPendingDelete(null)}
        title={t("delete")}
        description={t("confirmDelete", { title: pendingDelete?.name ?? "" })}
        confirmLabel={t("delete")}
        cancelLabel={t("cancel")}
        onConfirm={() => {
          if (pendingDelete) {
            return handleDelete(pendingDelete).finally(() => {
              setPendingDelete(null);
            });
          }
          setPendingDelete(null);
        }}
      />
      <Dialog
        open={Boolean(pendingRename)}
        onOpenChange={() => setPendingRename(null)}
      >
        <DialogContent>
          <DialogTitle>{t("rename")}</DialogTitle>
          <p className="text-sm text-muted-foreground">
            {t("renameDescription")}
          </p>
          <Input
            value={renameValue}
            onChange={(event) => setRenameValue(event.target.value)}
            placeholder={t("renamePlaceholder")}
            maxLength={80}
          />
          <DialogFooter>
            <Button variant="ghost" onClick={() => setPendingRename(null)}>
              {t("cancel")}
            </Button>
            <Button
              onClick={async () => {
                if (pendingRename) {
                  await handleRename(pendingRename, renameValue);
                }
                setPendingRename(null);
              }}
            >
              {t("save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </SidebarGroup>
  );
}
