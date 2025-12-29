import type { HistoryItem } from "@/shared/types/history";
import type { ChatModel } from "@/features/chat/types/chat";
import type { ToolGroupDefinition } from "@/shared/types/ui";
import type { UserInfo } from "@/shared/types/user";
import type { ThemeMode, PaletteMode } from "@/shared/types/theme";

/** Authz payload mirrored from the backend for tool gating and user data. */
export type AuthzState = {
  status: "idle" | "loading" | "success" | "error";
  tools: string[];
  toolGroups: ToolGroupDefinition[];
  user?: UserInfo;
  error?: string;
};

/** History list state used by the chat sidebar. */
export type HistoryState = {
  status: "idle" | "loading" | "success" | "error";
  items: HistoryItem[];
  continuationToken?: string | null;
  loadingMore?: boolean;
  error?: string;
};

/** Web search engine option returned by capabilities. */
export type WebSearchEngine = {
  id: string;
  name: string;
};

/** Model and tool capabilities returned from the backend. */
export type CapabilitiesState = {
  status: "idle" | "loading" | "success" | "error";
  models: ChatModel[];
  defaultModel: string;
  webSearchEngines: WebSearchEngine[];
  defaultWebSearchEngine: string;
  apiPageSizes: {
    messagesPageSizeDefault: number;
    messagesPageSizeMax: number;
    conversationsPageSizeDefault: number;
    conversationsPageSizeMax: number;
  };
  error?: string;
};

/** Persisted UI preferences stored in local storage. */
export type UiPreferencesSlice = {
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  palette: PaletteMode;
  setPalette: (palette: PaletteMode) => void;
  activeToolIds: string[];
  setActiveToolIds: (toolIds: string[]) => void;
  addActiveToolId: (toolId: string) => void;
  removeActiveToolId: (toolId: string) => void;
};

/** Authz state used to gate tools and show user identity in the sidebar. */
export type AuthzSlice = {
  authz: AuthzState;
  /** Fetches authz/tooling metadata that gates tools in the sidebar. */
  fetchAuthz: () => Promise<void>;
};

/** Conversation history state used by the sidebar list. */
export type HistorySlice = {
  history: HistoryState;
  /** Fetches conversation history for the sidebar list and updates ordering. */
  fetchHistory: (force?: boolean, merge?: boolean) => Promise<void>;
  fetchMoreHistory: () => Promise<void>;
  upsertHistoryItem: (item: HistoryItem) => void;
  removeHistoryItem: (url: string) => void;
};

/** Chat capabilities used for model and web search UI. */
export type CapabilitiesSlice = {
  capabilities: CapabilitiesState;
  /** Fetches model and web search capabilities for chat flows. */
  fetchCapabilities: () => Promise<void>;
};

/**
 * Global UI state for the app shell and data fetch lifecycles.
 *
 * Owns persisted preferences (theme, palette, active tools) and caches
 * backend-derived data (authz, history, capabilities) to avoid refetching
 * across routes.
 */
export type AppState = UiPreferencesSlice &
  AuthzSlice &
  HistorySlice &
  CapabilitiesSlice;
