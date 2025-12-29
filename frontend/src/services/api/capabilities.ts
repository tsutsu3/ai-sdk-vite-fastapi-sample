import type { ChatModel } from "@/features/chat/types/chat";
import { requestJson } from "@/lib/http/client";

/**
 * Capabilities payload returned by the backend.
 */
export type CapabilitiesResponse = {
  models?: ChatModel[];
  defaultModel?: string;
  webSearchEngines?: { id: string; name: string }[];
  defaultWebSearchEngine?: string;
  apiPageSizes?: {
    messagesPageSizeDefault?: number;
    messagesPageSizeMax?: number;
    conversationsPageSizeDefault?: number;
    conversationsPageSizeMax?: number;
  };
};

/**
 * Fetches model and web search capabilities.
 */
export async function fetchCapabilities(): Promise<CapabilitiesResponse> {
  const result = await requestJson<CapabilitiesResponse>("/api/capabilities");
  if (!result.ok) {
    throw new Error(`Failed to fetch capabilities: ${result.error.message}`);
  }
  return result.data;
}
