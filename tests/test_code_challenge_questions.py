import pytest
from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithoutReference,
    ResponseRelevancy,
    ResponseRelevancy,
)
from ragas.metrics._aspect_critic import SUPPORTED_ASPECTS
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from tests.shared.ragas_sample_test import sample_rag_chain
from app.rag_chain import create_rag_chain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader, UnstructuredPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_postgres import PGVector
from pathlib import Path

import os

EMBEDDINGS = {
    "openai": OpenAIEmbeddings(),
    "BAAI/bge-small": HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    ),
}

SHARED_PARAMS = {"embedding_model": "openai", "file_types": ["txt", "pdf"]}


@pytest.fixture(
    scope="class",
    params=[
        {
            **SHARED_PARAMS,
            "test_folder_name": "original_data",
        },
        {
            **SHARED_PARAMS,
            "test_folder_name": "modified_data",
        },
    ],
)
def setup_pgvector_db(request):
    """Fixture to populate PGVector database with variations in embedding, chunk size, and loaders."""
    db_url = os.getenv("POSTGRES_URL")
    params = request.param
    embedding_model = EMBEDDINGS[params["embedding_model"]]
    file_types = params["file_types"]
    test_folder_name = params["test_folder_name"]
    print(f"Setting up database with {embedding_model}")

    # Ensure database is cleared before each run
    DB = PGVector(embeddings=embedding_model, connection=db_url)
    DB.drop_tables()
    docs = []

    # read documents
    source_folder_path = Path(__file__).parent / "test_data" / test_folder_name
    saved_files = [file for file in source_folder_path.iterdir() if file.is_file()]
    for file_path in saved_files:
        if file_path.suffix.lower() == ".pdf" and "pdf" in file_types:
            loader = UnstructuredPDFLoader(str(file_path))
        elif file_path.suffix.lower() == ".txt" and "txt" in file_types:
            loader = TextLoader(str(file_path))
        else:
            print(f"Skipping unsupported file type: {file_path.suffix}")
            continue
        docs.extend(loader.load())
    if not docs:
        print("did not work")
        return {"message": "No valid documents found in uploaded files."}

    text_splitter = SemanticChunker(embeddings=embedding_model)
    chunks = text_splitter.split_documents(docs)
    DB.from_documents(
        documents=chunks,
        embedding=embedding_model,
        collection_name="test_collection",
        connection=db_url,
        pre_delete_collection=True,
    )

    yield {"embedding_model": embedding_model}

    # Optional: Cleanup after class tests complete


evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o"))
evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())


# Define metrics
metrics = SUPPORTED_ASPECTS + [
    Faithfulness(llm=evaluator_llm),
    LLMContextPrecisionWithoutReference(llm=evaluator_llm),
    ResponseRelevancy(llm=evaluator_llm),
    ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings),
]
# Example questions
questions_1 = [
    "Erkläre was die Firma EUBIA macht",
    "Was ist für die Bewerbung erforderlich? Liste alle Dokumente, Anforderungen und Voraussetzungen.",
    "Zitiere die genauen Anforderungen für die Bewerbung nach der Bewertungsmatrix?",
    "Basierend auf den Anforderungen, erstelle eine Gliederung für die Bewerbung.",
]
questions_2 = [
    "Zitiere die genauen Anforderungen für die Bewerbung nach der Bewertungsmatrix? Nenne bei jeder Anforderung die genaue Kriteriengewichtung.",
]
reference_1 = [
    "EUBIA bietet hochwertige, praxisorientierte Weiterbildungen für Fachkräfte an, um deren berufliche Kompetenzen zu stärken.",
    "Keine Referenz vorhanden, da komplexe Fragestellung.",
    "Keine Referenz vorhanden, da komplexe Fragestellung.",
    "Keine Referenz vorhanden, da komplexe Fragestellung.",
]


@pytest.mark.rag  # Custom marker for test categorization
class TestRAGCodeChallenge:
    """Test suite for the RAG chain execution."""

    def test_setup_db(self, setup_pgvector_db):
        """Fixture to ensure PGVector DB is set up before running tests."""
        self.pgvector_db = setup_pgvector_db  # This ensures DB is ready

    def test_rag_chain_execution(self, setup_pgvector_db):
        """Test the RAG chain execution for all questions in a single test."""
        final_chain = create_rag_chain(embedding_model=setup_pgvector_db["embedding_model"])
        result = sample_rag_chain(
            final_chain,
            questions_1,
            "test_collection",
            metrics,
        )

        # Assertions
        assert result is not None, "Result should not be None"

    def test_rag_chain_execution_2(self, setup_pgvector_db):
        """Test the RAG chain execution for a single extended detailed question."""
        final_chain = create_rag_chain(embedding_model=setup_pgvector_db["embedding_model"])
        result = sample_rag_chain(
            final_chain,
            questions_1 + questions_2,
            "test_collection",
            metrics,
        )

        # Assertions
        assert result is not None, "Result should not be None"


def test_db_setup(setup_pgvector_db):
    print("Setting up database")
    assert True
