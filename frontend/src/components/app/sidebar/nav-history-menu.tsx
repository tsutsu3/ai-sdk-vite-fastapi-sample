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
import { Link } from "react-router";
import type { HistoryItem } from "@/shared/types/history";
import { Separator } from "@radix-ui/react-separator";
import { ConfirmDeleteDialog } from "@/components/app/dialog/confirm-delete-dialog";
import type { RefObject } from "react";

export type NavHistoryMenuItem = HistoryItem & {
  isActive: boolean;
};

export type NavHistoryMenuViewModel = {
  label?: string;
  items: NavHistoryMenuItem[];
  scrollRef: RefObject<HTMLDivElement | null>;
  sentinelRef: RefObject<HTMLLIElement | null>;
  isMobile: boolean;
  t: (key: string, params?: Record<string, unknown>) => string;
  pendingDelete: HistoryItem | null;
  pendingRename: HistoryItem | null;
  renameValue: string;
  setPendingDelete: (item: HistoryItem | null) => void;
  setPendingRename: (item: HistoryItem | null) => void;
  setRenameValue: (value: string) => void;
  handleArchive: (item: HistoryItem) => Promise<void> | void;
  handleDelete: (item: HistoryItem) => Promise<void> | void;
  handleRename: (item: HistoryItem, nextTitle: string) => Promise<void> | void;
  formatUpdatedAt: (value: string) => string;
};

export type NavHistoryMenuProps = {
  viewModel: NavHistoryMenuViewModel;
};

export const NavHistoryMenu = ({ viewModel }: NavHistoryMenuProps) => {
  const {
    label,
    items,
    scrollRef,
    sentinelRef,
    isMobile,
    t,
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
  } = viewModel;

  return (
    <SidebarGroup className="flex min-h-0 flex-col group-data-[collapsible=icon]:hidden pr-0">
      {label && <SidebarGroupLabel>{label}</SidebarGroupLabel>}

      <div className="flex-1 overflow-y-auto" ref={scrollRef}>
        <SidebarMenu className="pr-4">
          {items.map((item) => (
            <SidebarMenuItem key={item.url}>
              <Tooltip delayDuration={500}>
                <TooltipTrigger asChild>
                  <SidebarMenuButton
                    asChild
                    isActive={item.isActive}
                  >
                    <Link to={item.url} className="flex-1">
                      <span>{item.name}</span>
                    </Link>
                  </SidebarMenuButton>
                </TooltipTrigger>
                <TooltipContent>
                  <div className="flex max-w-[40em] flex-col gap-1">
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
                  <Separator className="bg-sidebar-border my-1 h-px" />
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
          <li ref={sentinelRef} className="h-1" />
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
            return Promise.resolve(handleDelete(pendingDelete)).finally(() => {
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
          <p className="text-muted-foreground text-sm">
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
};
