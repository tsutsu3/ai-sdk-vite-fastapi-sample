from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory


def build_chat_chain(
    llm,
    *,
    history_factory,
    system_prompt: str = "You are a helpful assistant.",
) -> RunnableWithMessageHistory:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("history"),
            ("human", "{input}"),
        ]
    )
    chain = prompt | llm
    return RunnableWithMessageHistory(
        chain,
        history_factory,
        input_messages_key="input",
        history_messages_key="history",
    )
