/**
 * Represents an item in the conversation history list.
 *
 * Used by the sidebar to render recent chats and preserve ordering.
 */
export type HistoryItem = {
  /** Display name for the conversation. */
  name: string;
  /** Navigation URL for the conversation. */
  url: string;
  /** ISO timestamp for last update. */
  updatedAt: string;
};
