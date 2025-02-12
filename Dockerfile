FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0\
    poppler-utils\
    tesseract-ocr 

RUN pip install poetry==1.6.1
RUN poetry config virtualenvs.create false

WORKDIR /code

COPY ./pyproject.toml ./README.md ./poetry.lock* ./

COPY ./package[s] ./packages

RUN poetry install --no-interaction --no-ansi --no-root

COPY ./app ./app

RUN poetry install --no-interaction --no-ansi

# Ensure the directory exists
RUN mkdir -p /code/source_docs


EXPOSE 8080
ENV POSTGRES_URL="postgresql+psycopg://postgres@pgvector:5432/pdf_rag_vectors"


CMD exec uvicorn app.server:app --host 0.0.0.0 --port 8080
