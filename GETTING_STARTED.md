# Getting Started Guide

## Prerequisites

Before you begin, ensure you have the following:

1. **Docker and Docker Compose** (Recommended)
   - Docker: https://docs.docker.com/get-docker/
   - Docker Compose: https://docs.docker.com/compose/install/

2. **OpenAI API Key**
   - Sign up at https://platform.openai.com/
   - Create an API key in your account settings
   - You'll need this for embeddings and LLM functionality

## Step-by-Step Setup

### Option 1: Using Docker (Easiest)

1. **Clone the repository**
   ```bash
   git clone https://github.com/emmanueldeletang/RAGPOSTGRESQLFLASK.git
   cd RAGPOSTGRESQLFLASK
   ```

2. **Set up your environment**
   ```bash
   cp .env.example .env
   ```

3. **Edit the .env file and add your OpenAI API key**
   ```bash
   # Open .env in your favorite editor
   nano .env  # or vim, or any text editor
   
   # Change this line:
   OPENAI_API_KEY=your_openai_api_key_here
   
   # To your actual key:
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
   ```

4. **Start all services**
   ```bash
   docker-compose up --build
   ```
   
   This will start:
   - PostgreSQL with pgvector extension (port 5432)
   - Redis (port 6379)
   - Flask web application (port 5000)

5. **Access the application**
   - Open your browser and go to: http://localhost:5000
   - You should see the RAG Copilot interface

### Option 2: Manual Setup (Advanced)

#### Step 1: Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 2: Set up PostgreSQL with pgvector

**On Ubuntu/Debian:**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install pgvector
sudo apt install postgresql-15-pgvector

# Create database
sudo -u postgres psql
CREATE DATABASE ragdb;
CREATE USER raguser WITH PASSWORD 'ragpassword';
GRANT ALL PRIVILEGES ON DATABASE ragdb TO raguser;
\q

# Run initialization script
psql -U raguser -d ragdb -f init.sql
```

**On macOS (with Homebrew):**
```bash
# Install PostgreSQL
brew install postgresql@15
brew services start postgresql@15

# Install pgvector
brew install pgvector

# Create database
createdb ragdb
psql ragdb -f init.sql
```

**On Windows:**
- Download PostgreSQL from: https://www.postgresql.org/download/windows/
- Follow installation instructions
- Install pgvector: https://github.com/pgvector/pgvector#installation

#### Step 3: Set up Redis

**On Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
```

**On macOS:**
```bash
brew install redis
brew services start redis
```

**On Windows:**
- Download Redis from: https://github.com/microsoftarchive/redis/releases
- Or use Docker: `docker run -p 6379:6379 redis:7-alpine`

#### Step 4: Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

#### Step 5: Run the Application

```bash
python app.py
```

The application will be available at http://localhost:5000

## Testing the Application

### 1. Using the Web Interface

1. **Upload a document:**
   - Click the upload area or drag-and-drop a file
   - Try with a PDF, DOCX, or any supported format
   - Wait for the success message

2. **Ask questions:**
   - Type a question related to your document
   - Click "Send" or press Enter
   - View the AI-generated answer with sources

3. **Test caching:**
   - Ask the same question again
   - Notice the "⚡ Cached" badge indicating faster response
   - Cache can be from Redis (in-memory) or Database (persistent)

### 2. Using the API

```bash
# Health check
curl http://localhost:5000/api/health

# Upload a document
curl -X POST -F "file=@test.pdf" http://localhost:5000/api/upload

# Ask a question
curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'

# Get all documents
curl http://localhost:5000/api/documents

# Clear cache
curl -X POST http://localhost:5000/api/clear-cache
```

### 3. Using the Python Sample

```bash
# Create a test document first
echo "This is a test document about artificial intelligence and machine learning." > test.txt

# Run the sample code
python sample_usage.py
```

## Troubleshooting

### Docker Issues

**Problem: Port already in use**
```
Error: Bind for 0.0.0.0:5000 failed: port is already allocated
```
**Solution:** Change the port mapping in docker-compose.yml:
```yaml
ports:
  - "5001:5000"  # Changed from 5000:5000
```

**Problem: Database connection failed**
```
Error: could not connect to server
```
**Solution:** Wait for PostgreSQL to fully start (can take 30 seconds)
```bash
docker-compose logs postgres  # Check logs
```

### OpenAI API Issues

**Problem: OpenAI API key not set**
```
Error: The api_key client option must be set
```
**Solution:** Make sure you've set the OPENAI_API_KEY in your .env file

**Problem: Rate limit exceeded**
```
Error: Rate limit reached
```
**Solution:** 
- Wait a few minutes and try again
- Consider upgrading your OpenAI plan
- Reduce the number of chunks (increase CHUNK_SIZE in .env)

### Redis Issues

**Problem: Redis connection failed**
```
Error: Redis connection failed
```
**Solution:** The app will continue to work without Redis (just slower). To fix:
- Make sure Redis is running: `redis-cli ping` (should return "PONG")
- Check REDIS_HOST and REDIS_PORT in .env

### PostgreSQL Issues

**Problem: pgvector extension not available**
```
Error: extension "vector" is not available
```
**Solution:** Install pgvector extension for your PostgreSQL version
- See: https://github.com/pgvector/pgvector#installation

**Problem: Permission denied**
```
Error: permission denied to create extension "vector"
```
**Solution:** Grant superuser privileges or install extension manually:
```sql
-- As PostgreSQL superuser
psql ragdb
CREATE EXTENSION vector;
```

## Sample Test Documents

You can test the application with various document types:

1. **Create a test PDF**: Use any PDF file you have
2. **Create a test JSON**:
   ```json
   {
     "title": "AI Overview",
     "content": "Artificial Intelligence is transforming industries.",
     "topics": ["machine learning", "deep learning", "neural networks"]
   }
   ```
3. **Create a test CSV**:
   ```csv
   Topic,Description
   AI,Artificial Intelligence systems
   ML,Machine Learning algorithms
   DL,Deep Learning neural networks
   ```

## Next Steps

Once you have the application running:

1. Upload various document types to test compatibility
2. Experiment with different questions
3. Monitor the cache performance
4. Try the API endpoints programmatically
5. Customize the configuration in .env
6. Explore the source code to understand the architecture

## Getting Help

If you encounter issues:

1. Check the logs:
   ```bash
   # Docker
   docker-compose logs -f
   
   # Manual
   # Check terminal output where you ran app.py
   ```

2. Verify services are running:
   ```bash
   # PostgreSQL
   psql -U raguser -d ragdb -c "SELECT 1;"
   
   # Redis
   redis-cli ping
   ```

3. Test OpenAI connection:
   ```python
   from openai import OpenAI
   client = OpenAI(api_key="your-key")
   response = client.chat.completions.create(
       model="gpt-3.5-turbo",
       messages=[{"role": "user", "content": "Hello"}]
   )
   print(response.choices[0].message.content)
   ```

## Production Deployment

For production use:

1. Use strong passwords in .env
2. Set FLASK_DEBUG=False
3. Use a production WSGI server (gunicorn, uWSGI)
4. Set up HTTPS with nginx or similar
5. Implement authentication and authorization
6. Set up monitoring and logging
7. Regular database backups
8. Consider using managed services (AWS RDS, ElastiCache, etc.)

Happy building! 🚀
