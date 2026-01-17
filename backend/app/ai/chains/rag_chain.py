from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnableParallel


def build_rag_chain(llm, retriever, *, system_prompt: str = "", include_history: bool = True):
    system_text = system_prompt.strip() or "Answer using the provided sources only."
    messages: list[tuple[str, str] | MessagesPlaceholder] = [
        ("system", system_text),
    ]
    if include_history:
        messages.append(MessagesPlaceholder("history"))
    messages.append(("human", "Question: {question}\n\nSources:\n{context}"))
    prompt = ChatPromptTemplate.from_messages(messages)
    return (
        RunnableParallel(
            context=RunnableLambda(lambda x: x["question"])
            | retriever
            | RunnableLambda(_format_docs),
            question=RunnableLambda(lambda x: x["question"]),
            history=RunnableLambda(lambda x: x.get("history", [])),
            follow_up_questions_prompt=RunnableLambda(
                lambda x: x.get("follow_up_questions_prompt", "")
            ),
            injected_prompt=RunnableLambda(lambda x: x.get("injected_prompt", "")),
        )
        | prompt
        | llm
    )


def _format_docs(docs: list[Document]) -> str:
    blocks: list[str] = []
    for index, doc in enumerate(docs, start=1):
        title = doc.metadata.get("title") or f"Result {index}"
        url = doc.metadata.get("url") or ""
        text = doc.page_content or ""
        blocks.append(f"{index}. {title}\n{url}\n{text}".strip())
    return "\n\n".join(blocks)
