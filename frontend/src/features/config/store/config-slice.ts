import type { StateCreator } from "zustand";

import type { AppState, ConfigSlice } from "@/store/app-store.types";
import { fetchConfig, updateConfig } from "@/services/api/config";

const normalizeConfigPayload = (payload?: {
  tenantIds?: string[];
  activeTenantId?: string;
  tenants?: { id: string; name: string; key?: string | null }[];
}) => ({
  tenantIds: Array.isArray(payload?.tenantIds) ? payload?.tenantIds ?? [] : [],
  activeTenantId:
    typeof payload?.activeTenantId === "string" ? payload.activeTenantId : "",
  tenants: Array.isArray(payload?.tenants) ? payload.tenants ?? [] : [],
});

export const createConfigSlice: StateCreator<AppState, [], [], ConfigSlice> = (
  set,
  get,
) => ({
  config: {
    status: "idle",
    tenantIds: [],
    activeTenantId: "",
    tenants: [],
  },
  fetchConfig: async (force = false) => {
    const { config } = get();
    if (!force && (config.status === "loading" || config.status === "success")) {
      return;
    }
    set({ config: { ...config, status: "loading", error: undefined } });
    try {
      const payload = await fetchConfig();
      const normalized = normalizeConfigPayload(payload);
      set({
        config: {
          status: "success",
          tenantIds: normalized.tenantIds,
          activeTenantId: normalized.activeTenantId,
          tenants: normalized.tenants,
        },
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to load config";
      set({
        config: {
          status: "error",
          tenantIds: [],
          activeTenantId: "",
          tenants: [],
          error: message,
        },
      });
    }
  },
  setActiveTenant: async (tenantId: string) => {
    const { config } = get();
    if (!tenantId || tenantId === config.activeTenantId) {
      return;
    }
    set({
      config: {
        ...config,
        status: "updating",
        error: undefined,
      },
    });
    try {
      const payload = await updateConfig(tenantId);
      const normalized = normalizeConfigPayload(payload);
      set({
        config: {
          status: "success",
          tenantIds: normalized.tenantIds,
          activeTenantId: normalized.activeTenantId,
          tenants: normalized.tenants,
        },
      });
      await get().fetchAuthz(true);
      await get().fetchHistory(true, false);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to update tenant";
      set({
        config: {
          ...config,
          status: "error",
          error: message,
        },
      });
    }
  },
});
