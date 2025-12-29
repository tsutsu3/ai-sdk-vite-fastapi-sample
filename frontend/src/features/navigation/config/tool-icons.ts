import { Bot, SquareTerminal } from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * Icon mapping for tool groups returned by the backend.
 *
 * Keep keys aligned with tool group ids in authz responses.
 */
export const toolGroupIcons: Record<string, LucideIcon> = {
  rag01: SquareTerminal,
  rag02: Bot,
};
