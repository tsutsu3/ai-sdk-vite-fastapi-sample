import type { ToolGroupDefinition } from "@/shared/types/ui";
import type { UserInfo } from "@/shared/types/user";
import { requestJson } from "@/lib/http/client";

/**
 * Authz payload returned by the backend.
 */
export type AuthzResponse = {
  tools?: string[];
  toolGroups?: ToolGroupDefinition[];
  user?: UserInfo;
};

/**
 * Fetches authorization metadata and user identity.
 */
export async function fetchAuthz(): Promise<AuthzResponse> {
  const result = await requestJson<AuthzResponse>("/api/authz");
  if (!result.ok) {
    throw new Error(`Failed to fetch authz: ${result.error.message}`);
  }
  return result.data;
}
