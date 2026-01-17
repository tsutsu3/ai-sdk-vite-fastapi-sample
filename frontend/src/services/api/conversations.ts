import type { ChatMessageMetadata } from "@/features/chat/types/chat";
import { requestJson } from "@/lib/http/client";
import type { UIMessage } from "ai";

/**
 * Conversation metadata from the backend.
 */
export type ConversationApiItem = {
  id?: string;
  title?: string;
  toolId?: string | null;
  updatedAt?: string;
  createdAt?: string | null;
};

/**
 * Raw response shape for conversation list.
 */
type ConversationsResponse = {
  conversations?: ConversationApiItem[];
  continuationToken?: string | null;
};

/**
 * Raw response shape for conversation messages.
 */
type ConversationMessagesResponse = {
  messages?: UIMessage<ChatMessageMetadata>[];
  continuationToken?: string | null;
};

/**
 * Raw response shape for a single conversation update.
 */
export type ConversationDetailResponse = {
  id?: string;
  title?: string;
  toolId?: string | null;
  updatedAt?: string;
  createdAt?: string | null;
  messages?: UIMessage<ChatMessageMetadata>[];
};

/**
 * Fetches conversation summaries, optionally archived-only.
 */
export async function fetchConversations({
  archived,
  throwOnError = false,
  limit,
  continuationToken,
}: {
  archived?: boolean;
  throwOnError?: boolean;
  limit?: number;
  continuationToken?: string | null;
} = {}): Promise<{ conversations: ConversationApiItem[]; continuationToken: string | null }> {
  const params = new URLSearchParams();
  if (archived) {
    params.set("archived", "true");
  }
  if (typeof limit === "number") {
    params.set("limit", limit.toString());
  }
  if (continuationToken) {
    params.set("continuationToken", continuationToken);
  }
  const query = params.toString();
  const result = await requestJson<ConversationsResponse>(
    `/api/conversations${query ? `?${query}` : ""}`,
  );
  if (!result.ok) {
    if (throwOnError) {
      throw new Error(`Failed to fetch history: ${result.error.message}`);
    }
    return { conversations: [], continuationToken: null };
  }
  return {
    conversations: Array.isArray(result.data.conversations)
      ? result.data.conversations
      : [],
    continuationToken:
      typeof result.data.continuationToken === "string"
        ? result.data.continuationToken
        : null,
  };
}

/**
 * Fetches messages for a conversation.
 */
export async function fetchConversationMessages(
  conversationId: string,
  options?: {
    limit?: number;
    continuationToken?: string | null;
    signal?: AbortSignal;
  },
): Promise<{
  messages: UIMessage<ChatMessageMetadata>[];
  continuationToken: string | null;
}> {
  if (!conversationId) {
    return { messages: [], continuationToken: null };
  }
  const params = new URLSearchParams();
  if (typeof options?.limit === "number") {
    params.set("limit", options.limit.toString());
  }
  if (options?.continuationToken) {
    params.set("continuationToken", options.continuationToken);
  }
  const query = params.toString();
  const result = await requestJson<ConversationMessagesResponse>(
    `/api/conversations/${conversationId}/messages${query ? `?${query}` : ""}`,
    options?.signal ? { signal: options.signal } : undefined,
  );
  if (!result.ok) {
    return { messages: [], continuationToken: null };
  }
  return {
    messages: Array.isArray(result.data.messages) ? result.data.messages : [],
    continuationToken:
      typeof result.data.continuationToken === "string"
        ? result.data.continuationToken
        : null,
  };
}

/**
 * Updates a single conversation (e.g., archive/unarchive).
 */
export async function updateConversation(
  conversationId: string,
  updates: { archived?: boolean; title?: string },
): Promise<ConversationDetailResponse | null> {
  if (!conversationId) {
    return null;
  }
  const result = await requestJson<ConversationDetailResponse>(
    `/api/conversations/${conversationId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    },
  );
  if (!result.ok) {
    return null;
  }
  return result.data;
}

/**
 * Deletes a single conversation.
 */
export async function deleteConversation(
  conversationId: string,
): Promise<boolean> {
  if (!conversationId) {
    return false;
  }
  const response = await fetch(`/api/conversations/${conversationId}`, {
    method: "DELETE",
  });
  return response.ok;
}

/**
 * Updates all conversations (e.g., archive all).
 */
export async function updateAllConversations(updates: {
  archived?: boolean;
}): Promise<boolean> {
  const response = await fetch("/api/conversations", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  return response.ok;
}

/**
 * Deletes all conversations.
 */
export async function deleteAllConversations(): Promise<boolean> {
  const response = await fetch("/api/conversations", {
    method: "DELETE",
  });
  return response.ok;
}
