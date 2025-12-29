/**
 * Chat models selectable in the chat page.
 */
export type ChatModel = {
  /** Stable identifier sent to the backend. */
  id: string;
  /** Human-readable label displayed in the UI. */
  name: string;
  /** Grouping label shown in the selector. */
  chef: string;
  /** Logo slug for the primary provider. */
  chefSlug: string;
  /** Providers that can serve the model. */
  providers: string[];
};

// /**
//  * Supported chat stream status values.
//  *
//  * These map to UI states such as showing the loader, locking the input, or
//  * resuming normal interaction after a response completes.
//  */
// export type ChatStatus = "submitted" | "streaming" | "ready" | "error";

// /**
//  * A minimal message shape used by the chat view.
//  */
// export type ChatMessage = {
//   /** Unique message identifier. */
//   id: string;
//   /** Sender role. */
//   role: "user" | "assistant" | "system";
//   /** Message parts for rendering. */
//   parts: ChatMessagePart[];
//   /** Optional metadata for display and storage. */
//   metadata?: ChatMessageMetadata;
// };

/**
 * Message metadata used by the UI.
 */
export type ChatMessageMetadata = {
  /** File identifiers attached to the message. */
  fileIds?: string[];
  /** Model identifier used for assistant responses. */
  modelId?: string;
  /** Reaction captured in the UI. */
  reaction?: "like" | "dislike";
  /** Marks an assistant message as an error response. */
  isError?: boolean;
};

/**
 * A minimal message part shape for rendering text responses.
 *
 * The chat UI expects text parts to be present for assistant messages, with
 * other part types rendered by the AI elements components.
 */
export type ChatMessagePart = {
  /** Part type identifier. */
  type: string;
  /** Optional text content. */
  text?: string;
};
