DO $$ 
BEGIN 
  IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'pdf_rag_vectors') THEN 
    CREATE DATABASE pdf_rag_vectors; 
  END IF; 
END $$;
