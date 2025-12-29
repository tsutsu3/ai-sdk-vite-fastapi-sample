export async function updateMessageReaction(
  conversationId: string,
  messageId: string,
  reaction: "like" | "dislike" | null,
): Promise<{
  message?: {
    id?: string;
    metadata?: { reaction?: "like" | "dislike" | null };
  };
} | null> {
  if (!conversationId || !messageId) {
    return null;
  }
  const response = await fetch(
    `/api/conversations/${conversationId}/messages/${messageId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reaction }),
    },
  );
  if (!response.ok) {
    return null;
  }
  return response.json().catch(() => null);
}
