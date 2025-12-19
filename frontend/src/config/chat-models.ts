import type { ChatModel } from "@/types/chat";

/**
 * Default models for the chat experience.
 */
export const chatModels: ChatModel[] = [
  { id: "gpt-4o", name: "GPT-4o" },
  { id: "gpt-4o-mini", name: "GPT-4o mini" },
  { id: "gpt-5-mini", name: "GPT-5 mini" },
  { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash" },
];