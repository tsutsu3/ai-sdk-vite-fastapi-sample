import type { StateCreator } from "zustand";
import type { UiPreferencesSlice } from "@/store/app-store.types";

/**
 * UI preferences slice for persistent shell settings.
 *
 * Stores theme, palette, and active tool selection in the app store.
 */
export const createUiPreferencesSlice: StateCreator<UiPreferencesSlice> = (
  set,
) => ({
  theme: "system",
  setTheme: (theme) =>
    set((state) => (state.theme === theme ? state : { theme })),

  palette: "default",
  setPalette: (palette) =>
    set((state) => (state.palette === palette ? state : { palette })),

  activeToolIds: [],
  setActiveToolIds: (toolIds) =>
    set(() => ({ activeToolIds: Array.from(new Set(toolIds)) })),
  addActiveToolId: (toolId) =>
    set((state) =>
      state.activeToolIds.includes(toolId)
        ? state
        : { activeToolIds: [...state.activeToolIds, toolId] },
    ),
  removeActiveToolId: (toolId) =>
    set((state) => ({
      activeToolIds: state.activeToolIds.filter((id) => id !== toolId),
    })),
});
