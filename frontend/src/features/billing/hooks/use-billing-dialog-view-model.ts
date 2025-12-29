import { useMemo, useState } from "react";

export type BillingScope = "personal" | "tenant" | "tool";

export type BillingItem = {
  id: string;
  name: string;
  description: string;
  cost: string;
  usage: Array<{ label: string; value: string }>;
};

export const billingItems: BillingItem[] = [
  {
    id: "ai",
    name: "AI",
    description: "Tokens and model usage",
    cost: "$42.30",
    usage: [
      { label: "Tokens", value: "1.28M" },
      { label: "Models", value: "3" },
    ],
  },
  {
    id: "files",
    name: "File Storage",
    description: "Blob transfer + stored volume",
    cost: "$8.70",
    usage: [
      { label: "Transfer", value: "84.1 GB" },
      { label: "Stored", value: "412 GB" },
    ],
  },
  {
    id: "history",
    name: "Conversation History",
    description: "Cosmos RU + stored volume",
    cost: "$4.15",
    usage: [
      { label: "RU", value: "61.2k" },
      { label: "Stored", value: "18.2 GB" },
    ],
  },
  {
    id: "search",
    name: "Vector Search",
    description: "Semantic ranker calls",
    cost: "$6.84",
    usage: [
      { label: "Calls", value: "9,412" },
      { label: "Indexes", value: "4" },
    ],
  },
];

export const useBillingDialogViewModel = () => {
  const [scope, setScope] = useState<BillingScope>("personal");
  const [tenantId, setTenantId] = useState<string>("tenant-001");
  const [toolId, setToolId] = useState<string>("assistant");
  const [month, setMonth] = useState<string>("2025-12");

  const yesterday = useMemo(() => {
    const date = new Date();
    date.setDate(date.getDate() - 1);
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
    }).format(date);
  }, []);

  const chartData = useMemo(
    () =>
      billingItems.map((item) => ({
        id: item.id,
        name: item.name,
        cost: Number(item.cost.replace("$", "")) || 0,
        [item.id]: Number(item.cost.replace("$", "")) || 0,
      })),
    [],
  );

  return {
    scope,
    setScope,
    tenantId,
    setTenantId,
    toolId,
    setToolId,
    month,
    setMonth,
    yesterday,
    billingItems,
    chartData,
  };
};
