# Project Structure

```
RAGPOSTGRESQLFLASK/
│
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── database.py                 # Database operations and queries
│
├── app/                        # Application modules
│   ├── static/                 # Static files (CSS, JS)
│   │   ├── css/
│   │   │   └── style.css      # UI styling
│   │   └── js/
│   │       └── app.js         # Frontend JavaScript
│   │
│   ├── templates/              # HTML templates
│   │   └── index.html         # Main UI page
│   │
│   └── utils/                  # Utility modules
│       ├── __init__.py
│       ├── cache_service.py    # Redis caching
│       ├── document_processor.py  # File type handlers
│       ├── embedding_service.py   # OpenAI embeddings
│       ├── llm_service.py      # LLM interaction
│       └── text_chunker.py     # Text chunking logic
│
├── uploads/                    # Uploaded files directory
│   └── .gitkeep
│
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
│
├── Dockerfile                  # Docker container definition
├── docker-compose.yml         # Multi-container orchestration
├── init.sql                   # Database initialization
│
├── sample_usage.py            # API usage examples
├── test_app.py                # Unit tests
├── example_document.txt       # Sample document
│
├── README.md                  # Main documentation
├── QUICKSTART.md              # Quick start guide
├── GETTING_STARTED.md         # Detailed setup guide
├── API_DOCUMENTATION.md       # API reference
├── PROJECT_STRUCTURE.md       # This file
│
└── LICENSE                    # MIT License

```

## File Descriptions

### Core Application Files

#### `app.py`
Main Flask application with API endpoints:
- `/` - Web UI
- `/api/health` - Health check
- `/api/upload` - Document upload
- `/api/ask` - Question answering
- `/api/documents` - List documents
- `/api/clear-cache` - Clear cache

Key responsibilities:
- Route handling
- Request validation
- Service orchestration
- Error handling

#### `config.py`
Configuration management using environment variables:
- Database connection
- OpenAI API key
- Redis configuration
- Upload settings
- Chunking parameters
- LLM settings

#### `database.py`
PostgreSQL database operations:
- Connection management
- Schema initialization
- Document CRUD operations
- Vector similarity search
- Cache management

Key methods:
- `init_db()` - Create tables and indexes
- `insert_document()` - Store document
- `insert_chunk()` - Store chunk with embedding
- `search_similar_chunks()` - Vector search
- `get_cached_answer()` - Retrieve cached Q&A
- `cache_answer()` - Store Q&A

### Utility Modules

#### `app/utils/document_processor.py`
Extract text from various file formats:
- `process_pdf()` - PDF files
- `process_docx()` - Word documents
- `process_pptx()` - PowerPoint presentations
- `process_xlsx()` - Excel spreadsheets
- `process_csv()` - CSV files
- `process_json()` - JSON files
- `process_txt()` - Text files

#### `app/utils/text_chunker.py`
Split documents into chunks:
- Configurable chunk size
- Overlap for context continuity
- Smart boundary detection (sentences, paragraphs)

#### `app/utils/embedding_service.py`
Generate vector embeddings:
- OpenAI API integration
- Single and batch embedding generation
- Error handling and retries

#### `app/utils/llm_service.py`
LLM interaction for Q&A:
- Context-aware prompting
- Answer generation
- Temperature and token control

#### `app/utils/cache_service.py`
Redis caching layer:
- Fast in-memory cache
- Automatic expiration
- JSON serialization
- Graceful fallback

### Frontend Files

#### `app/templates/index.html`
Web interface structure:
- Upload section
- Document list
- Chat interface
- Status messages

#### `app/static/css/style.css`
UI styling:
- Modern gradient design
- Responsive layout
- Animations
- Message bubbles
- Upload area

#### `app/static/js/app.js`
Frontend logic:
- File upload handling
- Drag-and-drop support
- Question submission
- Real-time updates
- Cache management

### Configuration Files

#### `.env.example`
Environment variables template with all required settings and defaults.

#### `requirements.txt`
Python dependencies:
- Flask (web framework)
- psycopg2 (PostgreSQL)
- pgvector (vector extension)
- openai (embeddings & LLM)
- langchain (utilities)
- Document processing libraries
- Redis client

#### `docker-compose.yml`
Multi-container setup:
- PostgreSQL with pgvector
- Redis
- Flask application

Services are configured with health checks and proper dependencies.

#### `Dockerfile`
Flask application container:
- Python 3.11 base
- System dependencies
- Python packages
- Application code

#### `init.sql`
Database initialization:
- Enable pgvector extension
- Create tables (documents, document_chunks, qa_cache)
- Create indexes for performance

### Documentation Files

#### `README.md`
Comprehensive documentation:
- Feature overview
- Architecture diagram
- Installation instructions
- Usage examples
- Configuration guide

#### `QUICKSTART.md`
5-minute getting started guide:
- Minimal setup steps
- First document upload
- First question
- Quick troubleshooting

#### `GETTING_STARTED.md`
Detailed setup guide:
- Multiple installation methods
- Platform-specific instructions
- Troubleshooting
- Sample documents

#### `API_DOCUMENTATION.md`
Complete API reference:
- Endpoint documentation
- Request/response formats
- Code examples (Python, JavaScript)
- Error codes

### Testing & Examples

#### `test_app.py`
Unit tests for core components:
- Configuration loading
- Document processing
- Text chunking
- Caching
- Database operations

Run with: `python test_app.py`

#### `sample_usage.py`
Programmatic API usage examples:
- Upload documents
- Ask questions
- Handle responses
- Cache demonstration

Run with: `python sample_usage.py`

#### `example_document.txt`
Sample document about RAG systems for testing and demonstration.

## Data Flow

### Document Upload Flow
```
User uploads file
    ↓
app.py receives file
    ↓
document_processor.py extracts text
    ↓
text_chunker.py splits into chunks
    ↓
embedding_service.py generates embeddings
    ↓
database.py stores chunks + embeddings
    ↓
Return success to user
```

### Question Answering Flow
```
User asks question
    ↓
app.py receives question
    ↓
Check cache_service.py (Redis)
    ├─ Hit → Return cached answer
    └─ Miss ↓
Check database.py (PostgreSQL cache)
    ├─ Hit → Return cached answer, store in Redis
    └─ Miss ↓
embedding_service.py generates question embedding
    ↓
database.py searches similar chunks
    ↓
llm_service.py generates answer from context
    ↓
Cache answer in Redis + PostgreSQL
    ↓
Return answer to user
```

## Technology Stack by File

### Backend (Python)
- `app.py`, `config.py`, `database.py` - **Flask 3.0**
- `database.py` - **psycopg2** (PostgreSQL), **pgvector**
- `app/utils/cache_service.py` - **redis-py**
- `app/utils/embedding_service.py`, `app/utils/llm_service.py` - **OpenAI SDK**
- `app/utils/document_processor.py` - **pypdf**, **python-docx**, **python-pptx**, **openpyxl**, **pandas**
- `app/utils/text_chunker.py` - **Python standard library**

### Frontend
- `app/templates/index.html` - **HTML5**
- `app/static/css/style.css` - **CSS3** with modern features
- `app/static/js/app.js` - **Vanilla JavaScript** (ES6+)

### Infrastructure
- `Dockerfile`, `docker-compose.yml` - **Docker**
- `init.sql` - **PostgreSQL + pgvector**

## Key Design Decisions

1. **Modular Architecture**: Separate concerns into utility modules
2. **Dual Caching**: Redis for speed, PostgreSQL for persistence
3. **Vector Search**: pgvector for efficient similarity search
4. **No Framework Overhead**: Vanilla JS for simple, fast frontend
5. **Docker-First**: Easy deployment and consistency
6. **Environment-Based Config**: Flexible, secure configuration
7. **Graceful Degradation**: Works without Redis if unavailable

## Extension Points

To extend the application:

1. **Add File Types**: Edit `document_processor.py`, add handler
2. **Customize Chunking**: Modify `text_chunker.py` logic
3. **Change LLM**: Update `llm_service.py` and `embedding_service.py`
4. **Add Authentication**: Wrap endpoints in `app.py`
5. **Add Webhooks**: Create new routes in `app.py`
6. **Improve UI**: Edit `index.html`, `style.css`, `app.js`
7. **Add Logging**: Import logging in relevant modules
8. **Add Monitoring**: Integrate APM tools in `app.py`

## Dependencies Graph

```
app.py
  ├─ config.py
  ├─ database.py
  │   └─ config.py
  └─ app/utils/
      ├─ document_processor.py
      ├─ text_chunker.py
      ├─ embedding_service.py
      │   └─ config.py
      ├─ llm_service.py
      │   └─ config.py
      └─ cache_service.py
          └─ config.py
```

## Security Considerations

- **Environment Variables**: Secrets in `.env`, never in code
- **Input Validation**: File type and size checks in `app.py`
- **SQL Injection**: Parameterized queries in `database.py`
- **CORS**: Configured in `app.py` for API access
- **File Upload**: Secure filename handling with `werkzeug`

## Performance Optimization

- **Vector Index**: IVFFlat index for fast similarity search
- **Redis Cache**: Sub-second response for cached queries
- **Batch Embeddings**: Process multiple chunks at once
- **Connection Pooling**: PostgreSQL connection reuse
- **Chunking Strategy**: Balance between context and search precision

## Deployment Checklist

- [ ] Set strong passwords in `.env`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Use production WSGI server (gunicorn)
- [ ] Set up HTTPS
- [ ] Configure firewall
- [ ] Enable PostgreSQL backups
- [ ] Monitor logs
- [ ] Set up alerts
- [ ] Scale Redis and PostgreSQL as needed
- [ ] Implement rate limiting

## Maintenance

Regular tasks:
- Monitor OpenAI API usage
- Check PostgreSQL disk space
- Review Redis memory usage
- Update dependencies
- Review logs for errors
- Backup database

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify services: Health endpoints
3. Review documentation
4. Check environment variables
5. Test with example document
