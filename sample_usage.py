"""
Sample code demonstrating how to use the RAG application programmatically
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:5000"

def upload_document(file_path):
    """
    Upload a document to the RAG system
    
    Args:
        file_path: Path to the file to upload
        
    Returns:
        Response data from the API
    """
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
        return response.json()

def ask_question(question):
    """
    Ask a question to the RAG system
    
    Args:
        question: The question to ask
        
    Returns:
        Response data including answer and sources
    """
    data = {'question': question}
    response = requests.post(
        f"{BASE_URL}/api/ask",
        headers={'Content-Type': 'application/json'},
        json=data
    )
    return response.json()

def get_documents():
    """
    Get list of all uploaded documents
    
    Returns:
        List of documents
    """
    response = requests.get(f"{BASE_URL}/api/documents")
    return response.json()

def clear_cache():
    """
    Clear the Q&A cache
    
    Returns:
        Response data
    """
    response = requests.post(f"{BASE_URL}/api/clear-cache")
    return response.json()

# Example usage
if __name__ == "__main__":
    import os
    
    # Check if example document exists
    example_file = "example_document.txt"
    if not os.path.exists(example_file):
        print(f"Error: {example_file} not found.")
        print("Please create a document to upload or use an existing file.")
        print("\nExample: Create a simple text file")
        print("  echo 'This is a test document about AI.' > test.txt")
        print("  python sample_usage.py")
        exit(1)
    
    # 1. Upload a document
    print(f"Uploading document: {example_file}...")
    try:
        result = upload_document(example_file)
        print(f"Upload result: {result}")
    except FileNotFoundError:
        print(f"Error: File '{example_file}' not found. Please provide a valid file path.")
        exit(1)
    except Exception as e:
        print(f"Error uploading document: {e}")
        exit(1)
    
    # 2. Ask a question
    print("\nAsking a question...")
    question = "What is the main topic of the document?"
    result = ask_question(question)
    print(f"Question: {question}")
    print(f"Answer: {result['answer']}")
    print(f"Cached: {result.get('cached', False)}")
    
    if 'sources' in result:
        print("\nSources:")
        for source in result['sources']:
            print(f"  - {source['filename']} ({source['similarity']:.2%} match)")
    
    # 3. Get all documents
    print("\nGetting all documents...")
    docs = get_documents()
    print(f"Total documents: {len(docs.get('documents', []))}")
    
    # 4. Ask the same question again (should be cached)
    print("\nAsking the same question again...")
    result = ask_question(question)
    print(f"Answer: {result['answer']}")
    print(f"Cached: {result.get('cached', False)}")
    print(f"Cache source: {result.get('source', 'N/A')}")
