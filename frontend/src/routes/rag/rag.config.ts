export type RagConfig = {
  id: string;
  title: string;
  description: string;
};

export const ragConfigs: Record<string, RagConfig> = {
  rag0101: {
    id: "rag0101",
    title: "RAG01-01",
    description: "Test navigation-focused retrieval responses.",
  },
  rag0102: {
    id: "rag0102",
    title: "RAG01-02",
    description: "Reference-based retrieval.",
  },
  rag0201: {
    id: "rag0201",
    title: "RAG02-01",
    description: "News-oriented retrieval.",
  },
  rag0202: {
    id: "rag0202",
    title: "RAG02-02",
    description: "Product information retrieval.",
  },
  rag0203: {
    id: "rag0203",
    title: "RAG02-03",
    description: "FAQ-based retrieval.",
  },
};
