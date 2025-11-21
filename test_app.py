"""
Tests for the RAG application components
Note: These tests require OpenAI API key and running PostgreSQL/Redis instances
"""

import unittest
import os
from config import Config
from database import Database
from app.utils.document_processor import DocumentProcessor
from app.utils.text_chunker import TextChunker
from app.utils.cache_service import CacheService

class TestConfig(unittest.TestCase):
    """Test configuration loading"""
    
    def test_config_loads(self):
        """Test that configuration loads correctly"""
        config = Config()
        self.assertIsNotNone(config.DATABASE_URL)
        self.assertIsNotNone(config.UPLOAD_FOLDER)
        self.assertEqual(config.CHUNK_SIZE, 1000)
        self.assertEqual(config.CHUNK_OVERLAP, 200)

class TestDocumentProcessor(unittest.TestCase):
    """Test document processing"""
    
    def setUp(self):
        self.processor = DocumentProcessor()
    
    def test_process_txt(self):
        """Test TXT file processing"""
        # Create a test file
        test_file = '/tmp/test.txt'
        with open(test_file, 'w') as f:
            f.write("This is a test document.")
        
        content = self.processor.process_file(test_file, 'txt')
        self.assertEqual(content, "This is a test document.")
        
        # Cleanup
        os.remove(test_file)
    
    def test_process_json(self):
        """Test JSON file processing"""
        import json
        test_file = '/tmp/test.json'
        test_data = {"key": "value", "number": 42}
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        content = self.processor.process_file(test_file, 'json')
        self.assertIn("key", content)
        self.assertIn("value", content)
        
        # Cleanup
        os.remove(test_file)

class TestTextChunker(unittest.TestCase):
    """Test text chunking"""
    
    def setUp(self):
        self.chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    
    def test_chunk_text(self):
        """Test text chunking"""
        text = "This is a test. " * 50  # 800 characters
        chunks = self.chunker.chunk_text(text)
        
        self.assertGreater(len(chunks), 0)
        self.assertLessEqual(max(len(c) for c in chunks), 120)  # Some tolerance
    
    def test_empty_text(self):
        """Test chunking empty text"""
        chunks = self.chunker.chunk_text("")
        self.assertEqual(len(chunks), 0)
    
    def test_short_text(self):
        """Test chunking text shorter than chunk size"""
        text = "Short text"
        chunks = self.chunker.chunk_text(text)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)

class TestCacheService(unittest.TestCase):
    """Test caching service"""
    
    def setUp(self):
        self.cache = CacheService()
    
    def test_cache_set_get(self):
        """Test setting and getting cache"""
        if not self.cache.enabled:
            self.skipTest("Redis not available")
        
        key = "test_key"
        value = {"answer": "test answer", "context": "test context"}
        
        self.cache.set(key, value)
        retrieved = self.cache.get(key)
        
        self.assertEqual(retrieved, value)
    
    def test_cache_delete(self):
        """Test deleting from cache"""
        if not self.cache.enabled:
            self.skipTest("Redis not available")
        
        key = "test_key_delete"
        value = {"data": "test"}
        
        self.cache.set(key, value)
        self.cache.delete(key)
        retrieved = self.cache.get(key)
        
        self.assertIsNone(retrieved)

class TestDatabase(unittest.TestCase):
    """Test database operations"""
    
    def setUp(self):
        self.db = Database()
        try:
            self.db.init_db()
            self.db_available = True
        except Exception as e:
            print(f"Database not available: {e}")
            self.db_available = False
    
    def test_database_connection(self):
        """Test database connection"""
        if not self.db_available:
            self.skipTest("Database not available")
        
        conn = self.db.get_connection()
        self.assertIsNotNone(conn)
        conn.close()
    
    def test_insert_document(self):
        """Test inserting a document"""
        if not self.db_available:
            self.skipTest("Database not available")
        
        doc_id = self.db.insert_document(
            filename="test.txt",
            file_type="txt",
            content="Test content"
        )
        self.assertIsNotNone(doc_id)
        self.assertIsInstance(doc_id, int)
    
    def test_get_all_documents(self):
        """Test getting all documents"""
        if not self.db_available:
            self.skipTest("Database not available")
        
        docs = self.db.get_all_documents()
        self.assertIsInstance(docs, list)

def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)

if __name__ == "__main__":
    print("Running RAG Application Tests")
    print("=" * 50)
    print("\nNote: Some tests require:")
    print("- PostgreSQL with pgvector running")
    print("- Redis running")
    print("- OpenAI API key configured")
    print("\n" + "=" * 50 + "\n")
    
    run_tests()
