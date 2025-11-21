import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from config import Config
from database import Database
from app.utils.document_processor import DocumentProcessor
from app.utils.text_chunker import TextChunker
from app.utils.embedding_service import EmbeddingService
from app.utils.llm_service import LLMService
from app.utils.cache_service import CacheService

app = Flask(__name__, 
            template_folder='app/templates',
            static_folder='app/static')
app.config.from_object(Config)
CORS(app)

# Initialize services
db = Database()
doc_processor = DocumentProcessor()
text_chunker = TextChunker(
    chunk_size=app.config['CHUNK_SIZE'],
    chunk_overlap=app.config['CHUNK_OVERLAP']
)
embedding_service = EmbeddingService()
llm_service = LLMService()
cache_service = CacheService()

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'database': 'connected',
        'cache': 'enabled' if cache_service.enabled else 'disabled'
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and process a file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Get file type
        file_type = filename.rsplit('.', 1)[1].lower()
        
        # Process file and extract text
        text_content = doc_processor.process_file(file_path, file_type)
        
        # Insert document into database
        doc_id = db.insert_document(filename, file_type, text_content)
        
        # Chunk the text
        chunks = text_chunker.chunk_text(text_content)
        
        # Generate embeddings and store chunks
        for idx, chunk in enumerate(chunks):
            embedding = embedding_service.get_embedding(chunk)
            if embedding:
                db.insert_chunk(doc_id, chunk, idx, embedding)
        
        return jsonify({
            'message': 'File uploaded and processed successfully',
            'document_id': doc_id,
            'filename': filename,
            'chunks_created': len(chunks)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get all uploaded documents"""
    try:
        documents = db.get_all_documents()
        return jsonify({'documents': documents}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Ask a question and get an answer using RAG"""
    data = request.get_json()
    
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400
    
    question = data['question']
    
    try:
        # Check cache first (Redis)
        cache_key = f"qa:{question}"
        cached_result = cache_service.get(cache_key)
        
        if cached_result:
            return jsonify({
                'answer': cached_result['answer'],
                'context': cached_result['context'],
                'cached': True,
                'source': 'redis'
            }), 200
        
        # Check database cache
        db_cached = db.get_cached_answer(question)
        if db_cached:
            answer = db_cached['answer']
            context = db_cached['context']
            
            # Store in Redis cache for faster access next time
            cache_service.set(cache_key, {
                'answer': answer,
                'context': context
            })
            
            return jsonify({
                'answer': answer,
                'context': context,
                'cached': True,
                'source': 'database'
            }), 200
        
        # Generate embedding for the question
        question_embedding = embedding_service.get_embedding(question)
        
        # Search for similar chunks
        similar_chunks = db.search_similar_chunks(question_embedding, limit=5)
        
        if not similar_chunks:
            return jsonify({
                'answer': 'I could not find any relevant information to answer your question. Please upload some documents first.',
                'context': '',
                'cached': False
            }), 200
        
        # Combine similar chunks as context
        context = "\n\n".join([chunk['chunk_text'] for chunk in similar_chunks])
        
        # Generate answer using LLM
        answer = llm_service.generate_answer(question, context)
        
        # Cache the answer in both Redis and database
        cache_service.set(cache_key, {
            'answer': answer,
            'context': context
        })
        db.cache_answer(question, answer, context)
        
        return jsonify({
            'answer': answer,
            'context': context,
            'cached': False,
            'sources': [
                {
                    'filename': chunk['filename'],
                    'similarity': float(chunk['similarity'])
                }
                for chunk in similar_chunks
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """Clear all caches"""
    try:
        cache_service.clear_all()
        return jsonify({'message': 'Cache cleared successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    try:
        db.init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
    
    # Run app
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
