import type { StateCreator } from "zustand";
import type { AppState, HistorySlice } from "@/store/app-store.types";
import { fetchConversations } from "@/services/api/conversations";

const HISTORY_PAGE_SIZE = 50;

const resolveHistoryPageSize = (value?: number) =>
  typeof value === "number" && value > 0 ? value : HISTORY_PAGE_SIZE;

/**
 * History slice for conversation navigation.
 *
 * Fetches and maintains the sidebar chat history list.
 */
export const createHistorySlice: StateCreator<
  AppState,
  [],
  [],
  HistorySlice
> = (set, get) => ({
  history: {
    status: "idle",
    items: [],
    continuationToken: null,
    loadingMore: false,
  },
  // Powers the chat history list; errors leave the sidebar empty.
  fetchHistory: async (force = false, merge = true) => {
    const { history } = get();
    if (
      !force &&
      (history.status === "loading" || history.status === "success")
    ) {
      return;
    }
    set({
      history: { ...history, status: "loading", error: undefined },
    });
    try {
      if (get().capabilities.status === "idle") {
        await get().fetchCapabilities();
      } else if (get().capabilities.status === "loading") {
        await get().fetchCapabilities();
      }
      const result = await fetchConversations({
        throwOnError: true,
        limit: resolveHistoryPageSize(
          get().capabilities.apiPageSizes.conversationsPageSizeDefault,
        ),
        continuationToken: null,
      });
      const mapped = result.conversations.map((conversation) => ({
        name: conversation.title ?? "Conversation",
        url: `/chat/c/${conversation.id ?? crypto.randomUUID()}`,
        updatedAt: conversation.updatedAt ?? new Date().toISOString(),
      }));
      const known = history.items;
      const merged = merge
        ? [
            ...mapped,
            ...known.filter(
              (item) => !mapped.some((entry) => entry.url === item.url),
            ),
          ].sort(
            (a, b) =>
              new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
          )
        : mapped;
      set({
        history: {
          status: "success",
          items: merged,
          continuationToken: result.continuationToken,
          loadingMore: false,
        },
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to load history";
      set({
        history: {
          status: "error",
          items: [],
          error: message,
          continuationToken: null,
          loadingMore: false,
        },
      });
    }
  },
  fetchMoreHistory: async () => {
    const { history } = get();
    if (history.loadingMore || !history.continuationToken) {
      return;
    }
    set({
      history: {
        ...history,
        loadingMore: true,
      },
    });
    try {
      if (get().capabilities.status === "idle") {
        await get().fetchCapabilities();
      } else if (get().capabilities.status === "loading") {
        await get().fetchCapabilities();
      }
      const result = await fetchConversations({
        limit: resolveHistoryPageSize(
          get().capabilities.apiPageSizes.conversationsPageSizeDefault,
        ),
        continuationToken: history.continuationToken,
      });
      const mapped = result.conversations.map((conversation) => ({
        name: conversation.title ?? "Conversation",
        url: `/chat/c/${conversation.id ?? crypto.randomUUID()}`,
        updatedAt: conversation.updatedAt ?? new Date().toISOString(),
      }));
      set((state) => {
        const existingUrls = new Set(state.history.items.map((item) => item.url));
        const merged = state.history.items.concat(
          mapped.filter((item) => !existingUrls.has(item.url)),
        );
        return {
          history: {
            ...state.history,
            items: merged,
            continuationToken: result.continuationToken,
            loadingMore: false,
          },
        };
      });
    } catch {
      set((state) => ({
        history: {
          ...state.history,
          loadingMore: false,
        },
      }));
    }
  },
  upsertHistoryItem: (item) => {
    set((state) => {
      const existingIndex = state.history.items.findIndex(
        (entry) => entry.url === item.url,
      );
      const items = [...state.history.items];
      if (existingIndex >= 0) {
        items[existingIndex] = item;
      } else {
        items.unshift(item);
      }
      return {
        history: {
          ...state.history,
          items,
          status:
            state.history.status === "idle" ? "success" : state.history.status,
        },
      };
    });
  },
  removeHistoryItem: (url) => {
    set((state) => ({
      history: {
        ...state.history,
        items: state.history.items.filter((item) => item.url !== url),
      },
    }));
  },
});
