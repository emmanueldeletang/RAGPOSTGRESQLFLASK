# RAG Copilot - Document Q&A System 🤖

A full-stack web application that enables you to upload documents (CSV, JSON, Word, PowerPoint, Excel, PDF) and perform intelligent question-answering using Large Language Models (LLM) and vector search. Built with Flask, PostgreSQL + pgvector, OpenAI, and Redis for caching.

## ✨ Features

- **Multi-format Document Support**: Upload and process PDF, DOCX, PPTX, XLSX, CSV, JSON, and TXT files
- **Intelligent Vector Search**: Uses OpenAI embeddings and PostgreSQL pgvector for semantic search
- **LLM-Powered Q&A**: Generates accurate answers using GPT models based on your document content
- **Dual-Layer Caching**: Redis for fast in-memory caching and PostgreSQL for persistent cache
- **Modern Web UI**: Beautiful, responsive interface for uploading documents and asking questions
- **RESTful API**: Well-documented API endpoints for programmatic access
- **Docker Support**: Easy deployment with Docker Compose
- **Real-time Processing**: Automatic document chunking and embedding generation

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Web UI    │─────▶│  Flask API   │─────▶│  PostgreSQL │
│  (HTML/JS)  │      │              │      │  + pgvector │
└─────────────┘      └──────────────┘      └─────────────┘
                            │                      │
                            │                      │
                            ▼                      ▼
                     ┌──────────────┐      ┌─────────────┐
                     │    Redis     │      │   OpenAI    │
                     │   (Cache)    │      │ (Embeddings │
                     └──────────────┘      │  & LLM)     │
                                           └─────────────┘
```

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/emmanueldeletang/RAGPOSTGRESQLFLASK.git
   cd RAGPOSTGRESQLFLASK
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Web UI: http://localhost:5000
   - API: http://localhost:5000/api/health

### Manual Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL with pgvector**
   ```bash
   # Install PostgreSQL and pgvector extension
   # Then run the init.sql script to create tables
   psql -U postgres -d ragdb -f init.sql
   ```

3. **Set up Redis**
   ```bash
   # Install and start Redis
   redis-server
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

## 📖 Usage

### Web Interface

1. **Upload Documents**
   - Click the upload area or drag-and-drop files
   - Supported formats: PDF, DOCX, PPTX, XLSX, CSV, JSON, TXT
   - Documents are automatically processed and indexed

2. **Ask Questions**
   - Type your question in the chat input
   - The system searches through your documents
   - Receives AI-generated answers with source citations
   - Answers are cached for faster subsequent queries

### API Endpoints

#### Upload Document
```bash
POST /api/upload
Content-Type: multipart/form-data

curl -X POST -F "file=@document.pdf" http://localhost:5000/api/upload
```

Response:
```json
{
  "message": "File uploaded and processed successfully",
  "document_id": 1,
  "filename": "document.pdf",
  "chunks_created": 15
}
```

#### Ask Question
```bash
POST /api/ask
Content-Type: application/json

curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?"}'
```

Response:
```json
{
  "answer": "The main topic is...",
  "context": "Relevant excerpts from documents...",
  "cached": false,
  "sources": [
    {
      "filename": "document.pdf",
      "similarity": 0.89
    }
  ]
}
```

#### Get All Documents
```bash
GET /api/documents

curl http://localhost:5000/api/documents
```

#### Clear Cache
```bash
POST /api/clear-cache

curl -X POST http://localhost:5000/api/clear-cache
```

### Programmatic Usage

See `sample_usage.py` for examples:

```python
import requests

# Upload a document
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:5000/api/upload', files=files)
    print(response.json())

# Ask a question
data = {'question': 'What is the main topic?'}
response = requests.post(
    'http://localhost:5000/api/ask',
    json=data
)
print(response.json())
```

## 🔧 Configuration

All configuration is done through environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost:5432/ragdb` |
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `EMBEDDING_MODEL` | OpenAI embedding model | `text-embedding-ada-002` |
| `LLM_MODEL` | OpenAI LLM model | `gpt-3.5-turbo` |
| `CHUNK_SIZE` | Text chunk size | `1000` |
| `CHUNK_OVERLAP` | Chunk overlap size | `200` |

## 🏛️ Database Schema

### documents
- `id`: Primary key
- `filename`: Original filename
- `file_type`: File extension
- `content`: Extracted text content
- `created_at`: Upload timestamp

### document_chunks
- `id`: Primary key
- `document_id`: Foreign key to documents
- `chunk_text`: Text chunk
- `chunk_index`: Chunk position
- `embedding`: Vector embedding (1536 dimensions)
- `created_at`: Creation timestamp

### qa_cache
- `id`: Primary key
- `question`: Question text (unique)
- `answer`: Generated answer
- `context`: Context used for answer
- `created_at`: Creation timestamp

## 🛠️ Technology Stack

- **Backend**: Flask 3.0
- **Database**: PostgreSQL with pgvector extension
- **Cache**: Redis
- **AI/ML**: OpenAI (GPT-3.5-turbo, text-embedding-ada-002)
- **Document Processing**: pypdf, python-docx, python-pptx, openpyxl, pandas
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Deployment**: Docker, Docker Compose

## 📊 How It Works

1. **Document Upload**
   - User uploads a document through web UI or API
   - Document processor extracts text based on file type
   - Text is split into overlapping chunks (default: 1000 chars)
   - Each chunk is embedded using OpenAI embeddings
   - Chunks and embeddings are stored in PostgreSQL

2. **Question Answering**
   - User asks a question
   - System checks Redis cache, then PostgreSQL cache
   - If not cached, question is embedded using OpenAI
   - Vector similarity search finds relevant chunks
   - Context is assembled from top matching chunks
   - LLM generates answer based on context
   - Answer is cached in Redis and PostgreSQL

3. **Caching Strategy**
   - **Redis**: Fast in-memory cache (expires after 1 hour)
   - **PostgreSQL**: Persistent cache (never expires)
   - Cache key: Hash of the question
   - Significantly reduces API calls and response time

## 🎯 Use Cases

- **Internal Knowledge Base**: Search through company documents
- **Research Assistant**: Query academic papers and research materials
- **Document Analysis**: Extract insights from reports and presentations
- **Customer Support**: Build a copilot for support documentation
- **Legal/Compliance**: Search through contracts and policies
- **Education**: Interactive learning from course materials

## 🔒 Security Notes

- Store API keys in environment variables, never in code
- Use `.gitignore` to exclude sensitive files
- Implement authentication for production use
- Validate and sanitize user inputs
- Set appropriate file size limits

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT and embedding models
- pgvector for PostgreSQL vector extension
- Flask community for the excellent web framework 
