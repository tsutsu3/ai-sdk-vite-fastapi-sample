from collections.abc import AsyncIterator

from langchain_core.messages import AIMessageChunk, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory


class ChatRuntime:
    def __init__(self, runnable: RunnableWithMessageHistory, llm, history_factory) -> None:
        self._runnable = runnable
        self._llm = llm
        self._history_factory = history_factory

    async def stream_text(
        self,
        *,
        input_text: str,
        session_id: str,
    ) -> AsyncIterator[str]:
        async for chunk in self._runnable.astream(
            {"input": input_text},
            config={"configurable": {"session_id": session_id}},
        ):
            delta = _extract_text(chunk)
            if delta:
                yield delta

    async def stream_text_with_system(
        self,
        *,
        input_text: str,
        session_id: str,
        system_prompt: str,
    ) -> AsyncIterator[str]:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system}"),
                MessagesPlaceholder("history"),
                ("human", "{input}"),
            ]
        )
        chain = prompt | self._llm
        runnable = RunnableWithMessageHistory(
            chain,
            self._history_factory,
            input_messages_key="input",
            history_messages_key="history",
        )
        async for chunk in runnable.astream(
            {"input": input_text, "system": system_prompt},
            config={"configurable": {"session_id": session_id}},
        ):
            delta = _extract_text(chunk)
            if delta:
                yield delta


def _extract_text(chunk: BaseMessage | AIMessageChunk | str) -> str:
    if isinstance(chunk, str):
        return chunk
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return ""
