import { http, HttpResponse } from "msw";

const now = () => new Date().toISOString();

const mockUser = {
  user_id: "msw-user-001",
  email: "msw.user@example.com",
  provider: "msw",
  first_name: "Mika",
  last_name: "Suzuki",
};

// Match the IDs with those in navToolGroups in config/navigation.ts
const mockTools = ["rag01", "rag02"];

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
          })
        )
      );
      controller.enqueue(
        encoder.encode(
          data({
            type: "text-start",
            id: textId,
          })
        )
      );

      for (const token of tokens) {
        controller.enqueue(
          encoder.encode(
            data({
              type: "text-delta",
              id: textId,
              delta: `${token} `,
            })
          )
        );
      }

      controller.enqueue(
        encoder.encode(
          data({
            type: "text-end",
            id: textId,
          })
        )
      );
      controller.enqueue(
        encoder.encode(
          data({
            type: "finish",
            messageMetadata: {
              finishReason: "stop",
            },
          })
        )
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
    });
  }),

  http.get("/api/conversations", () => {
    return HttpResponse.json({
      conversations: mockConversations,
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
];
