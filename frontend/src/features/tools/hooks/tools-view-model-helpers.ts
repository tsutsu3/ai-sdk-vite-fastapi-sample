import type { RawDataEvent } from "@/features/chat/hooks/chat-view-model-helpers";
import { isRecord } from "@/features/chat/hooks/chat-view-model-helpers";
import type {
  ToolsChainOfThoughtStep,
  ToolsSourceItem,
} from "@/features/tools/hooks/tools-view-model-types";

export type ToolsChainOfThoughtEvent = {
  steps?: ToolsChainOfThoughtStep[];
  step?: ToolsChainOfThoughtStep;
  reset?: boolean;
  open?: boolean;
};

export type ToolsSourcesEvent = {
  sources?: ToolsSourceItem[];
  reset?: boolean;
};

export const isChainOfThoughtDataEvent = (
  event: RawDataEvent,
): event is { type: "data-cot"; data: ToolsChainOfThoughtEvent } => {
  return event.type === "data-cot" && isRecord(event.data);
};

export const isSourcesDataEvent = (
  event: RawDataEvent,
): event is { type: "data-sources"; data: ToolsSourcesEvent } => {
  return event.type === "data-sources" && isRecord(event.data);
};

export const mergeChainOfThoughtSteps = (
  current: ToolsChainOfThoughtStep[],
  incoming: ToolsChainOfThoughtEvent,
): ToolsChainOfThoughtStep[] => {
  if (incoming.reset) {
    return [];
  }
  if (Array.isArray(incoming.steps)) {
    return incoming.steps.filter(
      (step): step is ToolsChainOfThoughtStep =>
        isRecord(step) && typeof step.id === "string" && !!step.label,
    );
  }
  if (incoming.step && typeof incoming.step.id === "string") {
    const next = [...current];
    const index = next.findIndex((step) => step.id === incoming.step?.id);
    if (index >= 0) {
      next[index] = { ...next[index], ...incoming.step };
    } else {
      next.push(incoming.step);
    }
    return next;
  }
  return current;
};

export const mergeSources = (
  current: ToolsSourceItem[],
  incoming: ToolsSourcesEvent,
): ToolsSourceItem[] => {
  if (incoming.reset) {
    return [];
  }
  if (!Array.isArray(incoming.sources)) {
    return current;
  }
  return incoming.sources.filter(
    (source): source is ToolsSourceItem =>
      isRecord(source) && typeof source.id === "string" && !!source.title,
  );
};

export const buildToolsRequestBody = ({
  toolId,
  activeConversationId,
  hydeEnabled,
  maxDocuments,
}: {
  toolId: string;
  activeConversationId: string;
  hydeEnabled: boolean;
  maxDocuments?: number;
}) => {
  return {
    ...(toolId ? { tools: [toolId] } : {}),
    retrieval: {
      hyde: hydeEnabled,
      maxDocuments,
    },
    ...(activeConversationId ? { chatId: activeConversationId } : {}),
  };
};
