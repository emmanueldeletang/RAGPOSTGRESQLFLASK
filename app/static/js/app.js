// API base URL
const API_BASE = window.location.origin;

// DOM elements
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const uploadStatus = document.getElementById('uploadStatus');
const documentsList = document.getElementById('documentsList');
const chatContainer = document.getElementById('chatContainer');
const questionInput = document.getElementById('questionInput');
const askButton = document.getElementById('askButton');
const clearCacheButton = document.getElementById('clearCacheButton');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadDocuments();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // File upload
    fileInput.addEventListener('change', handleFileUpload);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#764ba2';
        uploadArea.style.background = '#f0f0ff';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#667eea';
        uploadArea.style.background = 'white';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#667eea';
        uploadArea.style.background = 'white';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileUpload();
        }
    });
    
    // Ask question
    askButton.addEventListener('click', askQuestion);
    questionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            askQuestion();
        }
    });
    
    // Clear cache
    clearCacheButton.addEventListener('click', clearCache);
}

// Handle file upload
async function handleFileUpload() {
    const files = fileInput.files;
    if (files.length === 0) return;
    
    for (let file of files) {
        await uploadFile(file);
    }
    
    // Clear input
    fileInput.value = '';
    
    // Reload documents list
    loadDocuments();
}

// Upload single file
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    showStatus('loading', `Uploading ${file.name}...`);
    
    try {
        const response = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus('success', `✓ ${file.name} uploaded successfully! Created ${data.chunks_created} chunks.`);
        } else {
            showStatus('error', `✗ Error uploading ${file.name}: ${data.error}`);
        }
    } catch (error) {
        showStatus('error', `✗ Error uploading ${file.name}: ${error.message}`);
    }
}

// Load documents list
async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE}/api/documents`);
        const data = await response.json();
        
        if (response.ok && data.documents && data.documents.length > 0) {
            displayDocuments(data.documents);
        } else {
            documentsList.innerHTML = '<p class="empty-state">No documents uploaded yet</p>';
        }
    } catch (error) {
        console.error('Error loading documents:', error);
        documentsList.innerHTML = '<p class="empty-state">Error loading documents</p>';
    }
}

// Display documents
function displayDocuments(documents) {
    documentsList.innerHTML = documents.map(doc => `
        <div class="document-item">
            <div class="document-info">
                <div class="document-name">📄 ${doc.filename}</div>
                <div class="document-meta">
                    Type: ${doc.file_type.toUpperCase()} | 
                    Uploaded: ${new Date(doc.created_at).toLocaleString()}
                </div>
            </div>
        </div>
    `).join('');
}

// Ask question
async function askQuestion() {
    const question = questionInput.value.trim();
    
    if (!question) {
        return;
    }
    
    // Disable input while processing
    questionInput.disabled = true;
    askButton.disabled = true;
    
    // Add user message to chat
    addMessage('user', question);
    
    // Clear input
    questionInput.value = '';
    
    // Show loading message
    const loadingId = addMessage('assistant', 'Thinking<span class="loading"></span>');
    
    try {
        const response = await fetch(`${API_BASE}/api/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });
        
        const data = await response.json();
        
        // Remove loading message
        removeMessage(loadingId);
        
        if (response.ok) {
            // Add assistant response
            addMessage('assistant', data.answer, {
                cached: data.cached,
                source: data.source,
                sources: data.sources
            });
        } else {
            addMessage('assistant', `Error: ${data.error}`);
        }
    } catch (error) {
        removeMessage(loadingId);
        addMessage('assistant', `Error: ${error.message}`);
    } finally {
        // Re-enable input
        questionInput.disabled = false;
        askButton.disabled = false;
        questionInput.focus();
    }
}

// Add message to chat
function addMessage(role, content, metadata = {}) {
    // Remove welcome message if it exists
    const welcomeMessage = chatContainer.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    const messageId = `msg-${Date.now()}`;
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `message ${role}`;
    
    let metaHtml = '';
    if (metadata.cached) {
        metaHtml += `<span class="cached-badge">⚡ Cached (${metadata.source})</span>`;
    }
    
    let sourcesHtml = '';
    if (metadata.sources && metadata.sources.length > 0) {
        sourcesHtml = `
            <div class="sources">
                <div class="sources-title">📚 Sources:</div>
                ${metadata.sources.map(s => `
                    <div class="source-item">
                        • ${s.filename} (${(s.similarity * 100).toFixed(1)}% match)
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">
            ${content}
            ${sourcesHtml}
        </div>
        <div class="message-meta">
            ${role === 'user' ? 'You' : 'AI Assistant'} • ${new Date().toLocaleTimeString()}
            ${metaHtml}
        </div>
    `;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return messageId;
}

// Remove message from chat
function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

// Clear cache
async function clearCache() {
    if (!confirm('Are you sure you want to clear the cache?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/clear-cache`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✓ Cache cleared successfully!');
        } else {
            alert(`✗ Error clearing cache: ${data.error}`);
        }
    } catch (error) {
        alert(`✗ Error clearing cache: ${error.message}`);
    }
}

// Show status message
function showStatus(type, message) {
    uploadStatus.className = `status-message ${type}`;
    uploadStatus.textContent = message;
    
    // Auto-hide after 5 seconds for success/error messages
    if (type !== 'loading') {
        setTimeout(() => {
            uploadStatus.style.display = 'none';
        }, 5000);
    }
}
