from pathlib import Path
from dotenv import load_dotenv
from langchain_postgres.vectorstores import PGVector
from llama_index.core import SimpleDirectoryReader
from langchain_core.documents import Document
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding  # ✅ Use LlamaIndex embedding for chunking
from langchain_openai import OpenAIEmbeddings  # ✅ Use LangChain embedding for PGVector

# Load environment variables
load_dotenv()

# Define document path
doc_path = Path(__file__).parent.parent / "source_docs" /

# Load documents
documents = SimpleDirectoryReader(input_dir=doc_path).load_data()

# ✅ Use LlamaIndex embedding for semantic chunking
llama_embedding = OpenAIEmbedding(model="text-embedding-ada-002")  

# Initialize the semantic chunker with LlamaIndex embedding
splitter = SemanticSplitterNodeParser(
    buffer_size=1,
    breakpoint_percentile_threshold=95,
    embed_model=llama_embedding  # ✅ Correct embedding for chunking
)

# Split the documents into nodes
nodes = splitter.get_nodes_from_documents(documents)

# Convert nodes to LangChain Documents
chunks = [Document(page_content=node.text, metadata=node.metadata) for node in nodes]

# ✅ Use LangChain embedding for PGVector storage
langchain_embedding = OpenAIEmbeddings(model="text-embedding-ada-002")  

# Store documents in PGVector with the correct embedding model
PGVector.from_documents(
    documents=chunks,
    embedding=langchain_embedding,  # ✅ Use LangChain embedding here
    collection_name="pdf_rag",
    connection="postgresql+psycopg://postgres@localhost:5432/pdf_rag_vectors",
    pre_delete_collection=True
)
