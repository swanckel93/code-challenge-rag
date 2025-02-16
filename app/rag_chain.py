import os
from operator import itemgetter
from typing_extensions import TypedDict, Any

from dotenv import load_dotenv
from langchain_postgres import PGVector
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnableLambda, Runnable
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.callbacks.base import BaseCallbackHandler

load_dotenv()


def get_retriever(collection_name: str, embedding_model):
    return PGVector(
        collection_name=collection_name,
        connection=os.getenv("POSTGRES_URL"),
        embeddings=embedding_model,
        async_mode=False,  # TODO : Set to false before dev
    ).as_retriever()


class StreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.partial_output = ""

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        self.partial_output += token
        print(token, end="", flush=True)


template = """
You are a chatbot that helps with answering questions. 
You shall answer the questions only on the context provided.
Avoid providing answers that are not relevant to the context.
Avoid providing answers that are not relevant to the question.
Answer the question in the language of the question.

Answer given the following context:
{context}

Question: {question}
"""

ANSWER_PROMPT = ChatPromptTemplate.from_template(template)


def format_prompt(inputs):
    """This function is used to fill in the template with the inputs"""
    return ANSWER_PROMPT.invoke(inputs)  # This fills in the template


llm = ChatOpenAI(temperature=0, model="gpt-4-1106-preview", streaming=True)


class RagInput(TypedDict):
    question: str
    collection_name: str  # Accept collection name dynamically


def create_rag_chain(embedding_model=OpenAIEmbeddings()) -> Runnable:
    return (
        RunnableParallel(
            context=RunnableLambda(
                lambda x: get_retriever(
                    x["collection_name"],
                    embedding_model=embedding_model,
                ).invoke(x["question"])
            ),
            question=itemgetter("question"),
        )
        | RunnableParallel(
            answer=(ANSWER_PROMPT | llm),
            docs=itemgetter("context"),
            filled_prompt=RunnableLambda(format_prompt),
        )
    ).with_types(input_type=RagInput)


final_chain = create_rag_chain()
