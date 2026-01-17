export type RagProgressStep = {
  id: string;
  label: string;
  description?: string;
  status?: "complete" | "active" | "pending";
  resultCount?: number;
  resultTitles?: string[];
};
