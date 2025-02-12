from pathlib import Path
import nltk
from langchain_community.document_loaders import DirectoryLoader, UnstructuredPDFLoader
from app.config import EMBEDDING_MODEL
from langchain_openai import OpenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from dotenv import load_dotenv
from langchain_postgres import PGVector
from app.config import PG_COLLECTION_NAME
import os
load_dotenv()
nltk.download('punkt')
nltk.download('punkt_tab')  # Explicitly download punkt_tab
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('averaged_perceptron_tagger_eng')

doc_path = Path(__file__).parent.parent / "source_docs" / "epic_vs_apple_documents"
loader = DirectoryLoader(
    str(doc_path),
    glob="*.pdf",
    # glob="20-5640_Epic_Games_Dkt_48_Order_Granting_in_Part_and_Denying_in_Part_Motion_for_a_Temporary_Restraining_Order.pdf",
    use_multithreading=True,
    show_progress=True,
    # max_concurrency=50,
    loader_cls=UnstructuredPDFLoader,
)

docs = loader.load()
embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, )

text_splitter = SemanticChunker(
    embeddings=embeddings
)

chunks = text_splitter.split_documents(docs)
print(os.getenv("POSTGRES_URL"))
PGVector.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name=PG_COLLECTION_NAME,
    connection="postgresql+psycopg://postgres@localhost:5432/pdf_rag_vectors",
    pre_delete_collection=True
)
