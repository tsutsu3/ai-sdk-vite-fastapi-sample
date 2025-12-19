"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type ThemeMode = "light" | "dark" | "system";

export type HistoryItem = {
  name: string;
  url: string;
  updatedAt: string;
};

type UserInfo = {
  user_id?: string;
  email?: string | null;
  provider?: string;
  first_name?: string | null;
  last_name?: string | null;
};

type AuthzState = {
  status: "idle" | "loading" | "success" | "error";
  tools: string[];
  user?: UserInfo;
  error?: string;
};

type HistoryState = {
  status: "idle" | "loading" | "success" | "error";
  items: HistoryItem[];
  error?: string;
};

type AppState = {
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;

  activeToolIds: string[];
  setActiveToolIds: (toolIds: string[]) => void;
  addActiveToolId: (toolId: string) => void;
  removeActiveToolId: (toolId: string) => void;

  authz: AuthzState;
  fetchAuthz: () => Promise<void>;

  history: HistoryState;
  fetchHistory: () => Promise<void>;
};

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      theme: "system",
      setTheme: (theme) =>
        set((state) => (state.theme === theme ? state : { theme })),

      activeToolIds: [],
      setActiveToolIds: (toolIds) =>
        set(() => ({ activeToolIds: Array.from(new Set(toolIds)) })),
      addActiveToolId: (toolId) =>
        set((state) =>
          state.activeToolIds.includes(toolId)
            ? state
            : { activeToolIds: [...state.activeToolIds, toolId] }
        ),
      removeActiveToolId: (toolId) =>
        set((state) => ({
          activeToolIds: state.activeToolIds.filter((id) => id !== toolId),
        })),

      authz: {
        status: "idle",
        tools: [],
      },
      fetchAuthz: async () => {
        const { authz } = get();
        if (authz.status === "loading" || authz.status === "success") {
          return;
        }
        set({ authz: { ...authz, status: "loading", error: undefined } });
        try {
          const response = await fetch("/api/authz");
          if (!response.ok) {
            throw new Error(`Failed to fetch authz: ${response.statusText}`);
          }
          const payload = await response.json();
          set({
            authz: {
              status: "success",
              tools: payload?.tools ?? [],
              user: payload?.user,
            },
          });
        } catch (error) {
          const message =
            error instanceof Error ? error.message : "Failed to load authz";
          set({
            authz: { status: "error", tools: [], error: message },
          });
        }
      },

      history: {
        status: "idle",
        items: [],
      },
      fetchHistory: async () => {
        const { history } = get();
        if (history.status === "loading" || history.status === "success") {
          return;
        }
        set({
          history: { ...history, status: "loading", error: undefined },
        });
        try {
          const response = await fetch("/api/conversations");
          if (!response.ok) {
            throw new Error(`Failed to fetch history: ${response.statusText}`);
          }
          const payload = await response.json();
          const conversations = payload?.conversations ?? [];
          const mapped = conversations.map((conversation: any) => ({
            name: conversation.title ?? "Conversation",
            url: `/chat/c/${conversation.id ?? crypto.randomUUID()}`,
            updatedAt: conversation.updatedAt ?? new Date().toISOString(),
          }));
          set({
            history: {
              status: "success",
              items: mapped,
            },
          });
        } catch (error) {
          const message =
            error instanceof Error ? error.message : "Failed to load history";
          set({
            history: { status: "error", items: [], error: message },
          });
        }
      },
    }),
    {
      name: "app-store",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        theme: state.theme,
        activeToolIds: state.activeToolIds,
      }),
    }
  )
);
