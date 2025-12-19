/**
 * Chat models selectable in the chat page.
 */
export type ChatModel = {
  /** Stable identifier sent to the backend. */
  id: string;
  /** Human-readable label displayed in the UI. */
  name: string;
};

/**
 * Supported chat stream status values.
 */
export type ChatStatus = "submitted" | "streaming" | "ready" | "error";

/**
 * A minimal message shape used by the chat view.
 */
export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  parts: ChatMessagePart[];
};

/**
 * A minimal message part shape for rendering text responses.
 */
export type ChatMessagePart = {
  type: string;
  text?: string;
};
