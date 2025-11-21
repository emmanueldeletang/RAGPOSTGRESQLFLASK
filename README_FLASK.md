# PostgreSQL Chat Application - Flask Version

A Flask-based web application for chatting with your data stored in PostgreSQL, featuring AI-powered responses using Azure OpenAI.

## Features

- **Chat Interface**: Interactive chat with AI assistant that queries your PostgreSQL database
- **Document Upload**: Upload and process PDF, Word, PowerPoint, Excel, CSV, and JSON files
- **Vector Search**: Semantic search using Azure OpenAI embeddings
- **Full-Text Search**: PostgreSQL full-text search capabilities
- **Hybrid Search**: Combination of vector and full-text search
- **System Prompt Management**: Customize AI assistant behavior
- **Response Caching**: Cache responses for faster retrieval
- **Argus Integration**: Import data from Azure Cosmos DB via Argus Accelerator

## Installation

1. **Create a virtual environment** (optional but recommended):
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**:
   ```powershell
   pip install -r requirements_flask.txt
   ```

3. **Configure environment variables**:
   - Copy `example.env` and update with your settings:
     - PostgreSQL connection details
     - Azure OpenAI credentials
     - Embedding model configuration

## Running the Application

1. **Start the Flask server**:
   ```powershell
   python pgtest.py
   ```

2. **Access the application**:
   - Open your browser and navigate to: `http://localhost:5000`

3. **Login**:
   - Enter your username, email, and country
   - This will create a user profile in the database

## Usage

### Initial Setup

1. **Configuration Page**: Navigate to Config to set up your database and Azure OpenAI settings
2. **Initialize Database**: Click "Initialize Database" to create required tables and indexes
3. **Upload Documents**: Go to the Upload page to add documents to your database

### Chatting with Your Data

1. **Select Search Type**: Choose between Vector, Full Text, or Hybrid search
2. **Ask Questions**: Type your questions in the chat input
3. **View Responses**: The AI will respond based on your uploaded data
4. **Cached Responses**: Previously asked questions will be retrieved from cache

### System Prompt Customization

1. **Navigate to System Prompt page**
2. **Edit the prompt**: Customize how the AI assistant behaves
3. **Use `{username}` placeholder**: This will be replaced with the actual username
4. **Save or Reset**: Save your custom prompt or reset to default

## File Structure

```
postgresqldemo/
├── pgtest.py                 # Main Flask application
├── requirements_flask.txt    # Python dependencies
├── example.env               # Environment configuration template
├── templates/                # HTML templates
│   ├── base.html            # Base template with navigation
│   ├── login.html           # Login page
│   ├── chat.html            # Chat interface
│   ├── upload.html          # File upload page
│   ├── config.html          # Configuration page
│   ├── system_prompt.html   # System prompt management
│   ├── files.html           # View uploaded files
│   └── argus.html           # Argus integration
└── uploads/                  # Temporary file storage
```

## API Endpoints

- `GET /`: Home page (redirects to chat)
- `GET, POST /login`: User login
- `GET /logout`: Logout user
- `GET /chat`: Chat interface
- `POST /send-message`: Send chat message (AJAX)
- `GET, POST /upload`: File upload page
- `GET, POST /config`: Configuration page
- `GET, POST /system-prompt`: System prompt management
- `GET /files`: List uploaded files
- `GET, POST /argus`: Argus integration page
- `POST /initialize`: Initialize database
- `POST /clear-cache`: Clear response cache
- `POST /clean-all`: Delete all tables

## Database Schema

### Tables

1. **tablecahedoc**: Stores cached AI responses with vector embeddings
2. **data**: Stores document chunks with vector embeddings
3. **userapp**: Stores user information
4. **system_prompts**: Stores custom system prompts per user

### Indexes

- DiskANN indexes for fast vector similarity search
- GIN indexes for full-text search

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: PostgreSQL with vector extensions
- **AI/ML**: Azure OpenAI (Chat & Embeddings)
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Document Processing**: LangChain, PyPDF, Docx2txt, Unstructured

## Migration from Streamlit

This application has been migrated from Streamlit to Flask for better customization and control. Key changes:

- **Session Management**: Flask session instead of st.session_state
- **Form Handling**: Standard HTML forms with POST requests
- **AJAX**: Used for chat messaging to avoid page reloads
- **Templates**: Jinja2 templates for server-side rendering
- **Static Assets**: Bootstrap for styling instead of Streamlit components

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check connection details in `example.env`
- Ensure PostgreSQL has vector extension installed

### Azure OpenAI Errors
- Verify API key and endpoint are correct
- Check API version compatibility
- Ensure you have quota for the models you're using

### File Upload Issues
- Check file size (max 16MB)
- Verify supported file format
- Ensure `uploads/` directory exists and is writable

## Credits

Made by Emmanuel Deletang  
Contact: edeletang@microsoft.com

## License

This project is provided as-is for demonstration purposes.
