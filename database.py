import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config

class Database:
    def __init__(self):
        self.config = Config()
        
    def get_connection(self):
        """Get a database connection"""
        return psycopg2.connect(self.config.DATABASE_URL, cursor_factory=RealDictCursor)
    
    def init_db(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # Enable pgvector extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create documents table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    file_type VARCHAR(50) NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create document chunks table with vector embeddings
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                    chunk_text TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    embedding vector(1536),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create index on embeddings for faster vector search
            try:
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
                    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """)
            except Exception as e:
                # Index might fail if not enough data, that's okay
                print(f"Index creation skipped: {e}")
            
            # Create QA cache table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS qa_cache (
                    id SERIAL PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(question)
                );
            """)
            
            # Create index on question for faster lookup
            cur.execute("""
                CREATE INDEX IF NOT EXISTS qa_cache_question_idx ON qa_cache(question);
            """)
            
            conn.commit()
            print("Database initialized successfully")
            
        except Exception as e:
            conn.rollback()
            print(f"Error initializing database: {e}")
            raise
        finally:
            cur.close()
            conn.close()
    
    def insert_document(self, filename, file_type, content):
        """Insert a new document and return its ID"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(
                "INSERT INTO documents (filename, file_type, content) VALUES (%s, %s, %s) RETURNING id;",
                (filename, file_type, content)
            )
            doc_id = cur.fetchone()['id']
            conn.commit()
            return doc_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    def insert_chunk(self, document_id, chunk_text, chunk_index, embedding):
        """Insert a document chunk with its embedding"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(
                "INSERT INTO document_chunks (document_id, chunk_text, chunk_index, embedding) VALUES (%s, %s, %s, %s);",
                (document_id, chunk_text, chunk_index, embedding)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    def search_similar_chunks(self, query_embedding, limit=5):
        """Search for similar chunks using vector similarity"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(
                """
                SELECT dc.chunk_text, dc.document_id, d.filename, 
                       1 - (dc.embedding <=> %s::vector) as similarity
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                ORDER BY dc.embedding <=> %s::vector
                LIMIT %s;
                """,
                (query_embedding, query_embedding, limit)
            )
            results = cur.fetchall()
            return results
        finally:
            cur.close()
            conn.close()
    
    def get_cached_answer(self, question):
        """Get cached answer for a question"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(
                "SELECT answer, context FROM qa_cache WHERE question = %s;",
                (question,)
            )
            result = cur.fetchone()
            return result
        finally:
            cur.close()
            conn.close()
    
    def cache_answer(self, question, answer, context):
        """Cache a question-answer pair"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(
                """
                INSERT INTO qa_cache (question, answer, context) 
                VALUES (%s, %s, %s)
                ON CONFLICT (question) 
                DO UPDATE SET answer = EXCLUDED.answer, context = EXCLUDED.context, created_at = CURRENT_TIMESTAMP;
                """,
                (question, answer, context)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    def get_all_documents(self):
        """Get all documents"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT id, filename, file_type, created_at FROM documents ORDER BY created_at DESC;")
            results = cur.fetchall()
            return results
        finally:
            cur.close()
            conn.close()
