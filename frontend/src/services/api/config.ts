import { requestJson } from "@/lib/http/client";
import type { UserInfo } from "@/shared/types/user";
import type { TenantSummary } from "@/shared/types/tenant";

export type ConfigResponse = {
  user?: UserInfo;
  tenantIds?: string[];
  activeTenantId?: string;
  tenants?: TenantSummary[];
};

export async function fetchConfig(): Promise<ConfigResponse> {
  const result = await requestJson<ConfigResponse>("/api/config");
  if (!result.ok) {
    throw new Error(`Failed to fetch config: ${result.error.message}`);
  }
  return result.data;
}

export async function updateConfig(
  activeTenantId: string,
): Promise<ConfigResponse> {
  const result = await requestJson<ConfigResponse>("/api/config", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ activeTenantId }),
  });
  if (!result.ok) {
    throw new Error(`Failed to update config: ${result.error.message}`);
  }
  return result.data;
}
