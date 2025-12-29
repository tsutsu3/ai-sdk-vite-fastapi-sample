import { http, HttpResponse } from "msw";

const now = () => new Date().toISOString();

const mockUser = {
  user_id: "msw-user-001",
  email: "msw.user@example.com",
  provider: "msw",
  first_name: "Mika",
  last_name: "Suzuki",
};

// Match the IDs with the backend tool groups.
const mockTools = ["rag01", "rag02"];
const mockToolGroups = [
  {
    id: "rag01",
    items: [{ id: "rag0101" }, { id: "rag0102" }],
  },
  {
    id: "rag02",
    items: [{ id: "rag0201" }, { id: "rag0202" }, { id: "rag0203" }],
  },
];

const mockConversations = [
  {
    id: "conv-quickstart",
    title: "Project kickoff chat",
    updatedAt: now(),
  },
  {
    id: "conv-rag",
    title: "RAG tuning ideas",
    updatedAt: now(),
  },
];

const mockArchivedConversations = [
  {
    id: "conv-archived-1",
    title: "Archived demo chat",
    updatedAt: now(),
    createdAt: now(),
  },
];

const mockMessagesByConversation: Record<
  string,
  Array<Record<string, unknown>>
> = {
  "conv-quickstart": [
    {
      id: "msg-system",
      role: "system",
      parts: [
        {
          type: "text",
          text: "You are a helpful project assistant.",
        },
      ],
    },
    {
      id: "msg-user-1",
      role: "user",
      parts: [
        {
          type: "text",
          text: "Please outline the next steps for our AI SDK demo.",
        },
      ],
    },
    {
      id: "msg-assistant-1",
      role: "assistant",
      parts: [
        {
          type: "text",
          text: "Sure! I will list the milestones and owners so you can start quickly.",
        },
      ],
    },
  ],
  "conv-rag": [
    {
      id: "msg-user-2",
      role: "user",
      parts: [
        {
          type: "text",
          text: "How can we improve retrieval quality for the docs index?",
        },
      ],
    },
    {
      id: "msg-assistant-2",
      role: "assistant",
      parts: [
        {
          type: "text",
          text: "Consider adding hierarchical chunking and reranking with a cross-encoder.",
        },
      ],
    },
  ],
};

const mockModels = [
  {
    id: "gpt-4o",
    name: "GPT-4o",
    chef: "OpenAI",
    chefSlug: "openai",
    providers: ["openai", "azure"],
  },
  {
    id: "gpt-4o-mini",
    name: "GPT-4o Mini",
    chef: "OpenAI",
    chefSlug: "openai",
    providers: ["openai", "azure"],
  },
];

const buildChatStream = (text: string) => {
  const encoder = new TextEncoder();
  const data = (payload: Record<string, unknown>) =>
    `data: ${JSON.stringify(payload)}\n\n`;
  const tokens = text.split(" ");

  return new ReadableStream({
    start(controller) {
      const messageId = `msg-${Date.now()}-${Math.random()
        .toString(16)
        .slice(2)}`;
      const textId = "text-1";

      controller.enqueue(
        encoder.encode(
          data({
            type: "start",
            messageId,
          }),
        ),
      );
      controller.enqueue(
        encoder.encode(
          data({
            type: "text-start",
            id: textId,
          }),
        ),
      );

      for (const token of tokens) {
        controller.enqueue(
          encoder.encode(
            data({
              type: "text-delta",
              id: textId,
              delta: `${token} `,
            }),
          ),
        );
      }

      controller.enqueue(
        encoder.encode(
          data({
            type: "text-end",
            id: textId,
          }),
        ),
      );
      controller.enqueue(
        encoder.encode(
          data({
            type: "finish",
            messageMetadata: {
              finishReason: "stop",
            },
          }),
        ),
      );
      controller.enqueue(encoder.encode("data: [DONE]\n\n"));
      controller.close();
    },
  });
};

export const handlers = [
  http.get("/api/authz", () => {
    return HttpResponse.json({
      user: mockUser,
      tools: mockTools,
      toolGroups: mockToolGroups,
    });
  }),

  http.get("/api/conversations", ({ request }) => {
    const url = new URL(request.url);
    const archived = url.searchParams.get("archived") === "true";
    return HttpResponse.json({
      conversations: archived ? mockArchivedConversations : mockConversations,
    });
  }),

  http.patch(
    "/api/conversations/:conversationId",
    async ({ request, params }) => {
      const conversationId =
        typeof params.conversationId === "string" ? params.conversationId : "";
      const body = await request.json().catch(() => null);
      const archived =
        body && typeof body === "object" && "archived" in body
          ? Boolean((body as Record<string, unknown>).archived)
          : false;
      const title =
        body && typeof body === "object" && "title" in body
          ? String((body as Record<string, unknown>).title ?? "")
          : undefined;
      if (!conversationId) {
        return new HttpResponse(null, { status: 404 });
      }
      const updatedAt = now();
      return HttpResponse.json({
        id: conversationId,
        title,
        archived,
        updatedAt,
        messages: [],
      });
    },
  ),

  http.patch("/api/conversations", async ({ request }) => {
    const body = await request.json().catch(() => null);
    const archived =
      body && typeof body === "object" && "archived" in body
        ? Boolean((body as Record<string, unknown>).archived)
        : false;
    const conversations = mockConversations.map((conversation) => ({
      ...conversation,
      archived,
      updatedAt: now(),
    }));
    return HttpResponse.json({ conversations });
  }),

  http.delete("/api/conversations", () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.delete("/api/conversations/:conversationId", ({ params }) => {
    const conversationId =
      typeof params.conversationId === "string" ? params.conversationId : "";
    if (!conversationId) {
      return new HttpResponse(null, { status: 404 });
    }
    return new HttpResponse(null, { status: 204 });
  }),

  http.get("/api/conversations/:conversationId/messages", ({ params }) => {
    const conversationId =
      typeof params.conversationId === "string" ? params.conversationId : "";
    return HttpResponse.json({
      messages: mockMessagesByConversation[conversationId] ?? [],
    });
  }),

  http.get("/api/capabilities", () => {
    return HttpResponse.json({
      models: mockModels,
    });
  }),

  http.post("/api/file", () => {
    return HttpResponse.json({
      fileId: `file-${Date.now()}`,
      contentType: "application/octet-stream",
      size: 0,
    });
  }),

  http.post("/api/chat", async ({ request }) => {
    const body = await request.json().catch(() => null);
    const model =
      body && typeof body === "object" && "model" in body
        ? (body.model as string | undefined)
        : undefined;
    const responseText = model
      ? `MSW mock response for model ${model}.`
      : "MSW mock response from the streaming chat endpoint.";

    return new HttpResponse(buildChatStream(responseText), {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
        "x-vercel-ai-ui-message-stream": "v1",
        "x-vercel-ai-protocol": "data",
      },
    });
  }),

  http.post("/chat", async ({ request }) => {
    const body = await request.json().catch(() => null);
    const model =
      body && typeof body === "object" && "model" in body
        ? (body.model as string | undefined)
        : undefined;
    const responseText = model
      ? `MSW mock response for model ${model}.`
      : "MSW mock response from the streaming chat endpoint.";

    return new HttpResponse(buildChatStream(responseText), {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
        "x-vercel-ai-ui-message-stream": "v1",
        "x-vercel-ai-protocol": "data",
      },
    });
  }),
];
