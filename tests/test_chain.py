import os
from operator import itemgetter
from typing_extensions import TypedDict

from dotenv import load_dotenv
from langchain_postgres import PGVector
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import PG_COLLECTION_NAME

load_dotenv()

vector_store = PGVector(
    collection_name=PG_COLLECTION_NAME,
    connection=os.getenv("POSTGRES_URL"),
    embeddings=OpenAIEmbeddings()
)

template = """
To answer the question, always use Markdown.
Only use Information from the context. Do not add any new information.
Answer given the following context:
{context}

Question: {question}
"""

ANSWER_PROMPT = ChatPromptTemplate.from_template(template)

llm = ChatOpenAI(temperature=0, model='gpt-4-1106-preview', streaming=True)


class RagInput(TypedDict):
    question: str



final_chain = (
        RunnableParallel(
            context=(itemgetter("question") | vector_store.as_retriever()),
            question=itemgetter("question")
        ) |
        RunnableParallel(
            answer=(ANSWER_PROMPT | llm),
            docs=itemgetter("context")
        )

).with_types(input_type=RagInput)
# print(final_chain.invoke({"question": "What is the case about?"}))
