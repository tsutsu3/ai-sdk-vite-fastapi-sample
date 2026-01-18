import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

import { createUiPreferencesSlice } from "@/shared/store/ui-preferences-slice";
import { createAuthzSlice } from "@/features/navigation/store/authz-slice";
import { createHistorySlice } from "@/features/chat/store/history-slice";
import { createCapabilitiesSlice } from "@/features/chat/store/capabilities-slice";
import { createConfigSlice } from "@/features/config/store/config-slice";
import type { AppState } from "@/store/app-store.types";

/**
 * Central Zustand store for shared UI state.
 *
 * Persists UI preferences and aggregates authz, history, and capabilities data.
 */
export const useAppStore = create<AppState>()(
  // TODO: Separate non-persistent state
  persist(
    (...args) => ({
      ...createUiPreferencesSlice(...args),
      ...createAuthzSlice(...args),
      ...createHistorySlice(...args),
      ...createCapabilitiesSlice(...args),
      ...createConfigSlice(...args),
    }),
    {
      name: "app-store",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        theme: state.theme,
        palette: state.palette,
        activeToolIds: state.activeToolIds,
      }),
    },
  ),
);
