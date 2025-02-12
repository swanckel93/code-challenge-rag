from fastapi import APIRouter, UploadFile, File, Form
from pathlib import Path
import shutil
import nltk
from langchain_community.document_loaders import TextLoader, UnstructuredPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_postgres import PGVector
from dotenv import load_dotenv
from app.config import EMBEDDING_MODEL, PG_COLLECTION_NAME
from sqlalchemy import create_engine, text
import os
# Ensure necessary NLTK dependencies are downloaded
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')
load_dotenv()
upload_router = APIRouter()
engine = create_engine(os.getenv("POSTGRES_URL"))

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

upload_router = APIRouter()

@upload_router.post("/upload_pdfs/")
async def upload_pdfs(
    collection_name: str = Form(...),
    files: list[UploadFile] = File(...),
):
    """Uploads PDFs and TXT files, extracts text, and stores embeddings in PGVector."""
    
    saved_files = []
    docs = []  # Store extracted documents
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    for file in files:
        filename = file.filename
        assert filename is not None

        file_path = Path(os.getenv("SOURCE_DOCS_DIR")) / filename  # Save permanently in source_docs
        print(file_path)
        # Check if file already exists
        if file_path.exists():
            print(f"Skipping {filename}, already exists.")
            continue  # Skip if the file is already present

        # Save the file permanently
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        saved_files.append(file_path)

    # Load and process each file based on type
    for file_path in saved_files:
        if file_path.suffix.lower() == ".pdf":
            loader = UnstructuredPDFLoader(str(file_path))
        elif file_path.suffix.lower() == ".txt":
            loader = TextLoader(str(file_path))
        else:
            print(f"Skipping unsupported file type: {file_path.suffix}")
            continue

        docs.extend(loader.load())

    if not docs:
        print("did not work")
        return {"message": "No valid documents found in uploaded files."}

    # Split into chunks
    text_splitter = SemanticChunker(embeddings=embeddings)
    chunks = text_splitter.split_documents(docs)

    # Store in PGVector
    PGVector.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        connection=os.getenv("POSTGRES_URL"),
        pre_delete_collection=True
    )

    return {
        "message": "Files uploaded and stored successfully.",
        "collection_name": collection_name
    }


@upload_router.get("/collections")
async def get_collections():
    """Fetches available collection names from PGVector."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT DISTINCT name FROM langchain_pg_collection"))
            collections = [row[0] for row in result.fetchall()]
            return collections
    except Exception as e:
        return {"error": f"Failed to retrieve collections: {str(e)}"}