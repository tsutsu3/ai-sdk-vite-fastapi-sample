import { useMemo } from "react";
import type { LucideIcon } from "lucide-react";
import { SquareTerminal } from "lucide-react";

import { useAppStore } from "@/store/app-store";
import { toolGroupIcons } from "@/features/navigation/config/tool-icons";

export type ToolCard = {
  id: string;
  path: string;
  labelKey: string;
  icon: LucideIcon;
};

export type ToolSection = {
  id: string;
  labelKey: string;
  items: ToolCard[];
};

export type HomeViewModel = {
  chatPath: string;
  toolSections: ToolSection[];
};

const buildToolGroupLabelKey = (groupId: string) =>
  `tool${groupId.replace(/^rag/i, "")}`;

const buildToolLabelKey = (toolId: string) =>
  `tool${toolId.replace(/^rag/i, "")}`;

export const useHomeViewModel = (): HomeViewModel => {
  const toolGroups = useAppStore((state) => state.authz.toolGroups);
  const allowedTools = useAppStore((state) => state.authz.tools);

  const toolSections = useMemo(() => {
    const allowedGroupIds = allowedTools.length ? allowedTools : undefined;
    return (toolGroups ?? [])
      .filter((group) =>
        allowedGroupIds ? allowedGroupIds.includes(group.id) : true,
      )
      .map((group) => {
        const icon = toolGroupIcons[group.id] ?? SquareTerminal;
        const items = (group.items ?? [])
          .filter((item) => typeof item?.id === "string" && item.id.length > 0)
          .map((item) => ({
            id: item.id,
            path: `/tools/${item.id}`,
            labelKey: buildToolLabelKey(item.id),
            icon,
          }));
        return {
          id: group.id,
          labelKey: buildToolGroupLabelKey(group.id),
          items,
        };
      })
      .filter((section) => section.items.length > 0);
  }, [toolGroups, allowedTools]);

  return {
    chatPath: "/chat",
    toolSections,
  };
};
