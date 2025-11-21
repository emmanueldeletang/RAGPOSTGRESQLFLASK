# Quick Start Example

This guide will get you up and running with the RAG Copilot in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key

## Steps

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/emmanueldeletang/RAGPOSTGRESQLFLASK.git
cd RAGPOSTGRESQLFLASK

# Set up environment
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### 2. Start Services

```bash
docker-compose up --build
```

Wait for all services to start (about 30 seconds). You should see:
```
web_1       | Database initialized successfully
web_1       | * Running on http://0.0.0.0:5000
```

### 3. Test the Application

Open your browser and navigate to:
```
http://localhost:5000
```

You should see the RAG Copilot interface.

### 4. Upload a Test Document

We've included an example document. Let's upload it:

**Using the Web UI:**
1. Click the upload area
2. Select `example_document.txt`
3. Wait for success message

**Using curl:**
```bash
curl -X POST -F "file=@example_document.txt" http://localhost:5000/api/upload
```

You should see:
```json
{
  "message": "File uploaded and processed successfully",
  "document_id": 1,
  "filename": "example_document.txt",
  "chunks_created": 5
}
```

### 5. Ask Your First Question

**Using the Web UI:**
1. Type a question: "What is RAG?"
2. Click Send or press Enter
3. View the AI-generated answer

**Using curl:**
```bash
curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?"}'
```

You should see:
```json
{
  "answer": "Retrieval-Augmented Generation (RAG) is an AI framework...",
  "context": "...",
  "cached": false,
  "sources": [
    {
      "filename": "example_document.txt",
      "similarity": 0.89
    }
  ]
}
```

### 6. Test Caching

Ask the same question again - it should be much faster and show `"cached": true`!

## Common Questions

**Q: What if I don't have an OpenAI API key?**
A: Sign up at https://platform.openai.com/ and create one. You'll need a paid account or free tier credits.

**Q: The upload is failing**
A: Check that:
- File size is under 16MB
- File format is supported (PDF, DOCX, PPTX, XLSX, CSV, JSON, TXT)
- You have enough disk space

**Q: Questions are not getting answers**
A: Make sure:
- You've uploaded at least one document
- Your OpenAI API key is valid
- You're not hitting rate limits

**Q: How do I stop the services?**
A: Press Ctrl+C in the terminal where docker-compose is running, then:
```bash
docker-compose down
```

## Next Steps

1. Upload your own documents
2. Try different question types
3. Explore the API (see API_DOCUMENTATION.md)
4. Check the comprehensive guides:
   - README.md - Full documentation
   - GETTING_STARTED.md - Detailed setup
   - API_DOCUMENTATION.md - API reference

## Sample API Workflow

Here's a complete Python example:

```python
import requests

BASE_URL = "http://localhost:5000"

# 1. Health check
response = requests.get(f"{BASE_URL}/api/health")
print("Health:", response.json())

# 2. Upload document
with open('example_document.txt', 'rb') as f:
    files = {'file': f}
    response = requests.post(f"{BASE_URL}/api/upload", files=files)
    print("Upload:", response.json())

# 3. Ask question
data = {"question": "What is RAG?"}
response = requests.post(f"{BASE_URL}/api/ask", json=data)
result = response.json()
print(f"Answer: {result['answer']}")
print(f"Cached: {result['cached']}")

# 4. Ask again (cached)
response = requests.post(f"{BASE_URL}/api/ask", json=data)
result = response.json()
print(f"Answer: {result['answer']}")
print(f"Cached: {result['cached']}")  # Should be True
print(f"Cache source: {result.get('source')}")  # redis or database
```

Save this as `quick_test.py` and run:
```bash
pip install requests
python quick_test.py
```

## Troubleshooting

**Container fails to start:**
```bash
docker-compose logs
```

**Database connection issues:**
```bash
docker-compose exec postgres psql -U raguser -d ragdb -c "SELECT 1;"
```

**Redis connection issues:**
```bash
docker-compose exec redis redis-cli ping
```

**Clear everything and restart:**
```bash
docker-compose down -v
docker-compose up --build
```

## Architecture Overview

```
┌─────────────┐
│   Browser   │
│   (You!)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Flask     │───▶│  PostgreSQL  │    │   OpenAI    │
│     +       │◀──▶│  + pgvector  │◀──▶│ Embeddings  │
│  REST API   │    └──────────────┘    │   & LLM     │
└─────────────┘                        └─────────────┘
       │
       ▼
┌─────────────┐
│    Redis    │
│   (Cache)   │
└─────────────┘
```

## What's Happening Under the Hood

1. **Upload:** File → Text extraction → Chunking → OpenAI embeddings → PostgreSQL storage
2. **Question:** Query → OpenAI embedding → Vector search → Top chunks → LLM answer → Cache
3. **Cached Query:** Query → Check Redis → Check PostgreSQL → Return instant answer

## Performance Tips

- First question: ~2-3 seconds (needs to generate embeddings and answer)
- Cached questions: ~50-100ms (from Redis) or ~200-300ms (from PostgreSQL)
- Larger documents: More chunks = slightly longer processing
- Rate limits: Free tier OpenAI has limits, consider upgrading for production

## Success!

You now have a fully functional RAG system! 🎉

Try uploading different types of documents and asking various questions. The system will get smarter as you add more content.

For production deployment and advanced configuration, see the other documentation files.
