import type { StateCreator } from "zustand";
import type { AppState, CapabilitiesSlice } from "@/store/app-store.types";
import { fetchCapabilities } from "@/services/api/capabilities";

/**
 * Capabilities slice for chat configuration.
 *
 * Loads available models and web search engines for the chat page.
 */
export const createCapabilitiesSlice: StateCreator<
  AppState,
  [],
  [],
  CapabilitiesSlice
> = (set, get) => ({
  capabilities: {
    status: "idle",
    models: [],
    defaultModel: "",
    webSearchEngines: [],
    defaultWebSearchEngine: "",
    apiPageSizes: {
      messagesPageSizeDefault: 30,
      messagesPageSizeMax: 200,
      conversationsPageSizeDefault: 50,
      conversationsPageSizeMax: 200,
    },
  },
  // Controls available models and web search toggles in the chat page.
  fetchCapabilities: async () => {
    const { capabilities } = get();
    if (
      capabilities.status === "loading" ||
      capabilities.status === "success"
    ) {
      return;
    }
    set({
      capabilities: { ...capabilities, status: "loading", error: undefined },
    });
    try {
      const payload = await fetchCapabilities();
      set({
        capabilities: {
          status: "success",
          models: Array.isArray(payload?.models) ? payload.models : [],
          defaultModel:
            typeof payload?.defaultModel === "string"
              ? payload.defaultModel
              : "",
          webSearchEngines: Array.isArray(payload?.webSearchEngines)
            ? payload.webSearchEngines
            : [],
          defaultWebSearchEngine:
            typeof payload?.defaultWebSearchEngine === "string"
              ? payload.defaultWebSearchEngine
              : "",
          apiPageSizes: {
            messagesPageSizeDefault:
              typeof payload?.apiPageSizes?.messagesPageSizeDefault === "number"
                ? payload.apiPageSizes.messagesPageSizeDefault
                : 30,
            messagesPageSizeMax:
              typeof payload?.apiPageSizes?.messagesPageSizeMax === "number"
                ? payload.apiPageSizes.messagesPageSizeMax
                : 200,
            conversationsPageSizeDefault:
              typeof payload?.apiPageSizes?.conversationsPageSizeDefault === "number"
                ? payload.apiPageSizes.conversationsPageSizeDefault
                : 50,
            conversationsPageSizeMax:
              typeof payload?.apiPageSizes?.conversationsPageSizeMax === "number"
                ? payload.apiPageSizes.conversationsPageSizeMax
                : 200,
          },
        },
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to load capabilities";
      set({
        capabilities: {
          status: "error",
          models: [],
          defaultModel: "",
          webSearchEngines: [],
          defaultWebSearchEngine: "",
          apiPageSizes: {
            messagesPageSizeDefault: 30,
            messagesPageSizeMax: 200,
            conversationsPageSizeDefault: 50,
            conversationsPageSizeMax: 200,
          },
          error: message,
        },
      });
    }
  },
});
