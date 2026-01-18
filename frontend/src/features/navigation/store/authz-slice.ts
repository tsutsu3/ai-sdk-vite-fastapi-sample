import type { StateCreator } from "zustand";
import type { AppState, AuthzSlice } from "@/store/app-store.types";
import { fetchAuthz } from "@/services/api/authz";

/**
 * Authz slice for tool gating and user identity.
 *
 * Keeps authorization state in sync with `/api/authz` for the sidebar and tool UI.
 */
export const createAuthzSlice: StateCreator<AppState, [], [], AuthzSlice> = (
  set,
  get,
) => ({
  authz: {
    status: "idle",
    tools: [],
    toolGroups: [],
  },
  // Drives tool gating and user identity shown in the sidebar.
  fetchAuthz: async (force = false) => {
    const { authz } = get();
    if (!force && (authz.status === "loading" || authz.status === "success")) {
      return;
    }
    set({ authz: { ...authz, status: "loading", error: undefined } });
    try {
      const payload = await fetchAuthz();
      set({
        authz: {
          status: "success",
          tools: payload?.tools ?? [],
          toolGroups: Array.isArray(payload?.toolGroups)
            ? payload.toolGroups
            : [],
          user: payload?.user,
        },
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to load authz";
      set({
        authz: { status: "error", tools: [], toolGroups: [], error: message },
      });
    }
  },
});
