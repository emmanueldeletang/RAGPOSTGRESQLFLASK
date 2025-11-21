# API Documentation

## Base URL
```
http://localhost:5000
```

## Endpoints

### Health Check

**GET** `/api/health`

Check the health status of the application.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "enabled"
}
```

**Example:**
```bash
curl http://localhost:5000/api/health
```

---

### Upload Document

**POST** `/api/upload`

Upload a document for processing and indexing.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Form data with file field

**Supported File Types:**
- PDF (`.pdf`)
- Word (`.docx`, `.doc`)
- PowerPoint (`.pptx`, `.ppt`)
- Excel (`.xlsx`, `.xls`)
- CSV (`.csv`)
- JSON (`.json`)
- Text (`.txt`)

**Response:**
```json
{
  "message": "File uploaded and processed successfully",
  "document_id": 1,
  "filename": "document.pdf",
  "chunks_created": 15
}
```

**Error Response:**
```json
{
  "error": "File type not allowed"
}
```

**Example:**
```bash
curl -X POST \
  http://localhost:5000/api/upload \
  -F "file=@/path/to/document.pdf"
```

**Python Example:**
```python
import requests

url = "http://localhost:5000/api/upload"
files = {'file': open('document.pdf', 'rb')}
response = requests.post(url, files=files)
print(response.json())
```

---

### Ask Question

**POST** `/api/ask`

Ask a question about uploaded documents.

**Request:**
- Method: `POST`
- Content-Type: `application/json`
- Body:
```json
{
  "question": "What is the main topic of the document?"
}
```

**Response (Uncached):**
```json
{
  "answer": "The main topic is RAG systems and their implementation...",
  "context": "Relevant excerpts from documents...",
  "cached": false,
  "sources": [
    {
      "filename": "document.pdf",
      "similarity": 0.89
    },
    {
      "filename": "overview.txt",
      "similarity": 0.85
    }
  ]
}
```

**Response (Cached):**
```json
{
  "answer": "The main topic is RAG systems...",
  "context": "Relevant excerpts...",
  "cached": true,
  "source": "redis"
}
```

**Error Response:**
```json
{
  "error": "No question provided"
}
```

**Example:**
```bash
curl -X POST \
  http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?"}'
```

**Python Example:**
```python
import requests

url = "http://localhost:5000/api/ask"
data = {"question": "What is RAG?"}
response = requests.post(url, json=data)
print(response.json())
```

---

### Get Documents

**GET** `/api/documents`

Get a list of all uploaded documents.

**Response:**
```json
{
  "documents": [
    {
      "id": 1,
      "filename": "document.pdf",
      "file_type": "pdf",
      "created_at": "2024-01-15T10:30:00"
    },
    {
      "id": 2,
      "filename": "overview.docx",
      "file_type": "docx",
      "created_at": "2024-01-15T11:45:00"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:5000/api/documents
```

**Python Example:**
```python
import requests

url = "http://localhost:5000/api/documents"
response = requests.get(url)
documents = response.json()['documents']

for doc in documents:
    print(f"{doc['filename']} - {doc['file_type']}")
```

---

### Clear Cache

**POST** `/api/clear-cache`

Clear all cached Q&A responses from Redis.

**Response:**
```json
{
  "message": "Cache cleared successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/clear-cache
```

**Python Example:**
```python
import requests

url = "http://localhost:5000/api/clear-cache"
response = requests.post(url)
print(response.json())
```

---

## Response Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully (document uploaded)
- `400 Bad Request`: Invalid request (missing parameters, invalid file type)
- `500 Internal Server Error`: Server error (database error, OpenAI API error)

---

## Rate Limiting

The application doesn't implement rate limiting by default, but it's recommended to add rate limiting in production. The OpenAI API has its own rate limits:

- Free tier: 3 requests/minute
- Pay-as-you-go: Higher limits based on usage

---

## Error Handling

All endpoints return JSON responses with an `error` field when something goes wrong:

```json
{
  "error": "Description of the error"
}
```

Common errors:
- `"No file provided"`: File not included in upload request
- `"File type not allowed"`: Unsupported file format
- `"No question provided"`: Question field missing or empty
- `"No API key"`: OpenAI API key not configured
- `"Database connection failed"`: Cannot connect to PostgreSQL
- `"Rate limit exceeded"`: OpenAI API rate limit reached

---

## Caching Behavior

The application uses a two-tier caching strategy:

1. **Redis Cache (L1)**
   - Fast in-memory cache
   - Expires after 1 hour by default
   - Returns `"source": "redis"` when hit

2. **Database Cache (L2)**
   - Persistent cache in PostgreSQL
   - Never expires
   - Returns `"source": "database"` when hit

When a question is asked:
1. Check Redis cache
2. If not found, check database cache
3. If not found, perform vector search and generate answer
4. Store result in both caches

---

## Best Practices

1. **File Size**: Keep uploads under 16MB (configurable)
2. **Question Format**: Ask specific, clear questions
3. **Document Quality**: Use text-based documents (not scanned images)
4. **API Key**: Keep OpenAI API key secure
5. **Batch Operations**: Upload multiple documents before asking questions
6. **Cache Management**: Clear cache when documents are updated

---

## Code Examples

### Complete Workflow Example

```python
import requests
import time

BASE_URL = "http://localhost:5000"

# 1. Check health
response = requests.get(f"{BASE_URL}/api/health")
print("Health:", response.json())

# 2. Upload documents
files_to_upload = ["doc1.pdf", "doc2.docx", "data.csv"]

for file_path in files_to_upload:
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
        print(f"Uploaded {file_path}:", response.json())
    time.sleep(1)  # Brief pause between uploads

# 3. Ask questions
questions = [
    "What is the main topic?",
    "Can you summarize the key points?",
    "What are the conclusions?"
]

for question in questions:
    data = {"question": question}
    response = requests.post(f"{BASE_URL}/api/ask", json=data)
    result = response.json()
    
    print(f"\nQ: {question}")
    print(f"A: {result['answer']}")
    print(f"Cached: {result.get('cached', False)}")
    
    if 'sources' in result:
        print("Sources:")
        for source in result['sources']:
            print(f"  - {source['filename']}")

# 4. Get all documents
response = requests.get(f"{BASE_URL}/api/documents")
documents = response.json()['documents']
print(f"\nTotal documents: {len(documents)}")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const BASE_URL = 'http://localhost:5000';

// Upload document
async function uploadDocument(filePath) {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(filePath));
  
  const response = await axios.post(`${BASE_URL}/api/upload`, formData, {
    headers: formData.getHeaders()
  });
  
  return response.data;
}

// Ask question
async function askQuestion(question) {
  const response = await axios.post(`${BASE_URL}/api/ask`, {
    question: question
  });
  
  return response.data;
}

// Usage
(async () => {
  try {
    // Upload
    const uploadResult = await uploadDocument('document.pdf');
    console.log('Upload:', uploadResult);
    
    // Ask
    const answer = await askQuestion('What is this document about?');
    console.log('Answer:', answer.answer);
    console.log('Cached:', answer.cached);
  } catch (error) {
    console.error('Error:', error.message);
  }
})();
```

---

## Webhooks (Future Feature)

Not currently implemented, but could be added for:
- Document processing completion notifications
- Daily usage reports
- Error alerts

---

## Monitoring

Monitor the application using:
- `/api/health` endpoint for uptime checks
- Application logs for errors
- Redis metrics for cache performance
- PostgreSQL query logs for slow queries
- OpenAI API usage dashboard

---

## Support

For issues or questions:
- Check the README.md
- Review GETTING_STARTED.md
- Check application logs
- Verify OpenAI API key and limits
- Ensure PostgreSQL and Redis are running
