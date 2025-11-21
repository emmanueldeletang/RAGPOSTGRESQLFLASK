from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import psycopg2
from dotenv import dotenv_values
from openai import AzureOpenAI
import json
import time
import uuid
import re
import csv
import string
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import AzureOpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_community.document_loaders import UnstructuredPowerPointLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tempfile import NamedTemporaryFile
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import UnstructuredExcelLoader
from azure.cosmos import CosmosClient, PartitionKey
import pandas as pd

env_name = "example.env"  # following example.env template change to your own .env file name
config = dotenv_values(env_name)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key_change_this_in_production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Default system prompt
DEFAULT_SYSTEM_PROMPT = '''
You are an intelligent assistant for yourdata, translate the answer in the same langage use for the ask. You are designed to provide answers to user questions about user's data.
You are friendly, helpful, and informative and can be lighthearted. Be concise in your responses.use the name of the file where the information is stored to provide the answer.
- start with the hello {username} - Only answer questions related to the information provided below.
'''

# Clear the cache table in the database
def clearcache(dbname, user, password, host, port):
    conn = get_db_connection(dbname, user, password, host, port)
    cur = conn.cursor()
    cur.execute('DELETE FROM tablecahedoc')
    conn.commit()
    cur.close()
    conn.close()

# Initialize the database with required tables and indexes
def intialize(dbname, user, password, host, port, embeddingssize, openai_embeddings_model):
    
# Connect to PostgreSQL
    conn = get_db_connection(dbname,user,password,host,port)
    cur = conn.cursor()

    # Execute a command: this creates a new table

    cur.execute('CREATE TABLE tablecahedoc (id serial PRIMARY KEY,'
                                 'prompt text  NOT NULL,'
                                 'completion text NOT NULL,'
                                 'completiontokens integer NOT NULL,'
                                 'promptTokens integer NOT NULL,'
                                 'totalTokens integer NOT NULL,'
                                 'model varchar(150) NOT NULL,'   
                                 'usname text NOT NULL,'
                                 'date_added date DEFAULT CURRENT_TIMESTAMP);'
        )


    cmd = """ALTER TABLE tablecahedoc  ADD COLUMN dvector vector("""+str(embeddingssize)+""")  GENERATED ALWAYS AS ( azure_openai.create_embeddings('"""+ str(openai_embeddings_model)+"""', prompt)::vector) STORED; """
    cur.execute(cmd)

    cm = """CREATE INDEX tablecahedoc_embedding_diskann_idx ON tablecahedoc USING diskann (dvector vector_cosine_ops)"""
    cur.execute(cm)

    cur.execute('CREATE TABLE data (id serial PRIMARY KEY,'
                                 'filename text NOT NULL,'
                                 'typefile text NOT NULL,' 
                                 'chuncks text,'
                                 'date_added date DEFAULT CURRENT_TIMESTAMP);'
                                 )
    

    
    cmd = """ALTER TABLE data  ADD COLUMN dvector vector("""+str(embeddingssize)+""")  GENERATED ALWAYS AS ( azure_openai.create_embeddings('"""+ str(openai_embeddings_model)+"""', chuncks)::vector) STORED; """
    cur.execute(cmd)

    cmd2 = """CREATE INDEX data_embedding_diskann_idx ON data USING diskann (dvector vector_cosine_ops)"""
    cur.execute(cmd2)
    
    cmd3 = """CREATE INDEX data_idx ON data USING GIN (to_tsvector('english', chuncks));"""
    cur.execute(cmd3)
    
    cur.execute('''CREATE TABLE IF NOT EXISTS system_prompts (
                    id serial PRIMARY KEY,
                    username text NOT NULL,
                    prompt_name text NOT NULL,
                    prompt_text text NOT NULL,
                    is_active boolean DEFAULT false,
                    date_added date DEFAULT CURRENT_TIMESTAMP);
                ''')
    
    cmd3 = """CREATE TABLE IF NOT EXISTS public.userapp(id serial PRIMARY KEY,username text ,email text NOT NULL , country text, date_added date DEFAULT CURRENT_TIMESTAMP);"""    
    cur.execute(cmd3)
    # Commit the transaction
    conn.commit()

# Close the cursor and connection
    cur.close()
    conn.close()

# Clean all tables from the database
def cleanall(dbname,user,password,host,port):

# Connect to PostgreSQL
    conn = get_db_connection(dbname,user,password,host,port)
    cur = conn.cursor()

    # Execute a command: this creates a new table

    cur.execute('DROP TABLE IF EXISTS tablecahedoc;')
    conn.commit()
    cur.execute('DROP TABLE IF EXISTS data;')
    conn.commit()
    cur.execute('DROP TABLE IF EXISTS system_prompts;')
    conn.commit()
    cur.execute('DROP TABLE IF EXISTS userapp;')
    conn.commit()
    cur.close()
    conn.close()

# Load a PowerPoint file into the database
def loadpptfile(name,file,dbname,user,password,host,port, upload_id=None) :
    
    if upload_id:
        upload_progress[upload_id] = {'status': 'processing', 'progress': 50, 'message': 'Loading PowerPoint...'}
    
    loader = UnstructuredPowerPointLoader(file)
    data = loader.load()
    
    if upload_id:
        upload_progress[upload_id] = {'status': 'processing', 'progress': 60, 'message': 'Splitting slides...'}
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = text_splitter.split_documents(data)
    
    if upload_id:
        upload_progress[upload_id] = {'status': 'processing', 'progress': 70, 'message': f'Inserting {len(docs)} chunks...'}
   
    try:
        total_docs = len(docs)
        for idx, d in enumerate(docs):
            data = str(d)
         
            conn = get_db_connection(dbname,user,password,host,port)
            cur = conn.cursor()
            cur.execute('INSERT INTO data (filename, typefile,chuncks)'
                        'VALUES (%s, %s,%s)',
                        (name,"ppt",data)
                        )
            conn.commit()
            cur.close()
            conn.close()
            
            if upload_id and total_docs > 0:
                progress = 70 + int((idx + 1) / total_docs * 25)
                upload_progress[upload_id] = {'status': 'processing', 'progress': progress, 'message': f'Inserted {idx + 1}/{total_docs} chunks...'}
    except : 
     raise 

# Load an Excel file into the database
def loadxlsfile(name,file,dbname,user,password,host,port, upload_id=None) :
    
    if upload_id:
        upload_progress[upload_id] = {'status': 'processing', 'progress': 50, 'message': 'Loading Excel file...'}
    
    loader = UnstructuredExcelLoader(file, mode="elements")
    data = loader.load()

    if upload_id:
        upload_progress[upload_id] = {'status': 'processing', 'progress': 60, 'message': 'Splitting data...'}
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = text_splitter.split_documents(data)
    
    if upload_id:
        upload_progress[upload_id] = {'status': 'processing', 'progress': 70, 'message': f'Inserting {len(data)} chunks...'}
      
    try:
        total_docs = len(data)
        for idx, d in enumerate(data):
            dat = str(d)
         
            conn = get_db_connection(dbname,user,password,host,port)
            cur = conn.cursor()
            cur.execute('INSERT INTO data (filename, typefile,chuncks)'
                        'VALUES (%s, %s,%s)',
                        (name,"xls",dat)
                        )
            conn.commit()
            cur.close()
            conn.close()
            
            if upload_id and total_docs > 0:
                progress = 70 + int((idx + 1) / total_docs * 25)
                upload_progress[upload_id] = {'status': 'processing', 'progress': progress, 'message': f'Inserted {idx + 1}/{total_docs} chunks...'}
    except : 
     raise 

# Load a generic file using Azure Document Intelligence

# Load a PDF file into the database
def loadpdffile(name,file,dbname,user,password,host,port, upload_id=None) :
    
    print(f"Loading PDF file: {file}")
    print(f"File exists: {os.path.exists(file)}")
   
    # Verify file exists before attempting to load
    if not os.path.exists(file):
        raise FileNotFoundError(f"PDF file not found: {file}")
    
    if upload_id:
        upload_progress[upload_id] = {'status': 'processing', 'progress': 50, 'message': 'Loading PDF document...'}
    
    try:
        loader = PyPDFLoader(file)
        data = loader.load()
    except Exception as e:
        print(f"Error in PyPDFLoader: {str(e)}")
        raise Exception(f"Failed to load PDF document. Make sure it's a valid PDF file. Error: {str(e)}")
    
    if upload_id:
        upload_progress[upload_id] = {'status': 'processing', 'progress': 60, 'message': 'Splitting document into chunks...'}
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = text_splitter.split_documents(data)
    
    if upload_id:
        upload_progress[upload_id] = {'status': 'processing', 'progress': 70, 'message': f'Inserting {len(docs)} chunks into database...'}
    
    try:
        total_docs = len(docs)
        for idx, d in enumerate(docs):
            data = str(d)
           
            conn = get_db_connection(dbname,user,password,host,port)
            cur = conn.cursor()
            cur.execute('INSERT INTO data (filename, typefile,chuncks)'
                        'VALUES (%s, %s,%s)',
                        (name,"pdf",data)
                        )
            conn.commit()
            cur.close()
            conn.close()
            
            if upload_id and total_docs > 0:
                progress = 70 + int((idx + 1) / total_docs * 25)
                upload_progress[upload_id] = {'status': 'processing', 'progress': progress, 'message': f'Inserted {idx + 1}/{total_docs} chunks...'}
    except : 
     raise     

# Load a Word file into the database
def loadwordfile(name,file,dbname,user,password,host,port, upload_id=None) :
    
    print(f"Loading Word file: {file}")
    print(f"File exists: {os.path.exists(file)}")
    
    from langchain_community.document_loaders import Docx2txtLoader
    
    # Verify file exists before attempting to load
    if not os.path.exists(file):
        raise FileNotFoundError(f"Word file not found: {file}")
    
    if upload_id:
        upload_progress[upload_id] = {'status': 'processing', 'progress': 50, 'message': 'Loading Word document...'}
    
    try:
        loader = Docx2txtLoader(file)
        data = loader.load()    
    except Exception as e:
        print(f"Error in Docx2txtLoader: {str(e)}")
        raise Exception(f"Failed to load Word document. Make sure it's a valid .docx file. Error: {str(e)}")
  
    if upload_id:
        upload_progress[upload_id] = {'status': 'processing', 'progress': 60, 'message': 'Splitting document...'}
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = text_splitter.split_documents(data)
   
    if upload_id:
        upload_progress[upload_id] = {'status': 'processing', 'progress': 70, 'message': f'Inserting {len(docs)} chunks...'}
    
    try:
        total_docs = len(docs)
        for idx, d in enumerate(docs):
            data = str(d)
            conn = get_db_connection(dbname,user,password,host,port)
            cur = conn.cursor()
            cur.execute('INSERT INTO data (filename, typefile,chuncks)'
                        'VALUES (%s, %s,%s)',
                        (name,"word",data)
                        )
            conn.commit()
            cur.close()
            conn.close()
            
            if upload_id and total_docs > 0:
                progress = 70 + int((idx + 1) / total_docs * 25)
                upload_progress[upload_id] = {'status': 'processing', 'progress': progress, 'message': f'Inserted {idx + 1}/{total_docs} chunks...'}
    except : 
     raise    

# Load a JSON file into the database
def loadjsonfile(name,file,dbname,user,password,host,port, upload_id=None): 
    
    if upload_id:
        upload_progress[upload_id] = {'status': 'processing', 'progress': 50, 'message': 'Reading JSON file...'}
    
    with open(file,encoding="utf8") as file:
        docu = json.load(file)
        total_rows = len(docu)
        
        if upload_id:
            upload_progress[upload_id] = {'status': 'processing', 'progress': 60, 'message': f'Inserting {total_rows} records...'}
        
        for idx, row in enumerate(docu):
            data = json.dumps(row)
            conn = get_db_connection(dbname,user,password,host,port)
            cur = conn.cursor()
            cur.execute('INSERT INTO data (filename, typefile,chuncks)'
                'VALUES (%s, %s,%s)',
                (name,"json",data)
               )
            conn.commit()
            cur.close()
            conn.close()
            
            if upload_id and total_rows > 0:
                progress = 60 + int((idx + 1) / total_rows * 35)
                upload_progress[upload_id] = {'status': 'processing', 'progress': progress, 'message': f'Inserted {idx + 1}/{total_rows} records...'}

# Load a CSV file into the database
def loadcsvfile(name,file,dbname,user,password,host,port, upload_id=None) :
    
 if upload_id:
     upload_progress[upload_id] = {'status': 'processing', 'progress': 50, 'message': 'Reading CSV file...'}
 
 with open(file, mode='r', encoding='utf-8-sig') as file:
  csv_reader = csv.DictReader(file)
  rows = list(csv_reader)
  total_rows = len(rows)
  
  if upload_id:
      upload_progress[upload_id] = {'status': 'processing', 'progress': 60, 'message': f'Inserting {total_rows} rows...'}
  
  for idx, row in enumerate(rows):
    data = json.dumps(row)
    conn = get_db_connection(dbname,user,password,host,port)
    cur = conn.cursor()
    cur.execute('INSERT INTO data (filename, typefile,chuncks)'
                'VALUES (%s, %s,%s)',
                (name,"csv",data)
               )
    conn.commit()
    cur.close()
    conn.close()
    
    if upload_id and total_rows > 0:
        progress = 60 + int((idx + 1) / total_rows * 35)
        upload_progress[upload_id] = {'status': 'processing', 'progress': progress, 'message': f'Inserted {idx + 1}/{total_rows} rows...'}
  

# Load data from Argus Accelerator into the database
def loaddataargus( argusdb,arguscollection , argusurl,arguskey, dbname,user,password,host,port) :
    
    clientargus = CosmosClient(argusurl, {'masterKey': arguskey})
    mydbtsource = clientargus.get_database_client(argusdb)   
     

    
    try:
        i = 0
        query = "SELECT c.id,c.extracted_data.gpt_summary_output FROM c WHERE c.extracted_data.gpt_summary_output != ''"
        source = mydbtsource.get_container_client(arguscollection)
        result = list( source.query_items(
            query=query,
            enable_cross_partition_query=True))

        for item in result:
            summary_output = item.get("gpt_summary_output")
            file = item.get("id")
            i = i+1
     
                     
            conn = get_db_connection(dbname,user,password,host,port)
            cur = conn.cursor()
            cur.execute('INSERT INTO data (filename, typefile,chuncks)'
                'VALUES (%s, %s,%s)',
                (file,"argus",summary_output)
               )
       
            conn.commit()
            cur.close()
            conn.close()

       
    except : 
        raise  
    return i 
    
# Get a completion from OpenAI
def get_completion(openai_client, model, prompt: str):    
   
    response = openai_client.chat.completions.create(
        model = model,
        messages =   prompt,
        temperature = 0.15
        
    )   
    
    return response.model_dump()

# Get a database connection
def get_db_connection(dbname,user,password,host,port):
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port)
    return conn

# Authenticate a user
def authenticate(username):
    # Pour des raisons de démonstration, nous utilisons une vérification simple
    return username 
    
# Generate a completion with OpenAI and enrich with database data
def generatecompletionede(openai_client,system_prompt,user_prompt ,username,dbname,user,password,host,port,openai_embeddings_model, openai_chat_model,typesearch) -> str:
    
 

    
    # system prompt

    messages = [{'role': 'system', 'content': system_prompt}]
    #user prompt
    messages.append({'role': 'user', 'content': user_prompt})
    
    vector_search_results =  ask_dbvector(user_prompt,dbname,user,password,host,port,openai_embeddings_model,typesearch )
    
    for result in vector_search_results:
     
        messages.append({'role': 'system', 'content': result})
    
    response = get_completion(openai_client, openai_chat_model, messages)

    return response

# Cache a response in the database
def cacheresponse(user_prompt,  response , name,dbname,user,password,host,port):

    
        
    conn = get_db_connection(dbname,user,password,host,port)
    cur = conn.cursor()
    cur.execute('INSERT INTO tablecahedoc (prompt, completion, completiontokens, promptTokens,totalTokens, model,usname)'
                    'VALUES (%s, %s, %s, %s ,%s, %s,%s)',
                    (user_prompt, response['choices'][0]['message']['content'], response['usage']['completion_tokens'], response['usage']['prompt_tokens'],response['usage']['total_tokens'], response['model'] ,name))
    


  
    conn.commit()
    cur.close()
    conn.close()

# Search the cache for a similar query
def cachesearch(test,name,dbname,user,password,host,port,openai_embeddings_model):
    conn = get_db_connection(dbname,user,password,host,port)
    cur = conn.cursor()
    
    print('userprompt cherche cache')
    print (test)
   
    query = """SELECT e.completion
    FROM tablecahedoc e  
    WHERE e.usname = %s 
    AND e.dvector <=> azure_openai.create_embeddings(%s, %s)::vector < 0.07  
    ORDER BY e.dvector <=> azure_openai.create_embeddings(%s, %s)::vector  
    LIMIT 1;"""
   
    cur.execute(query, (name, openai_embeddings_model, test, openai_embeddings_model, test))
    resutls = cur.fetchall()
   

  
    return resutls
    
# Query the database using vector or full-text search
def  ask_dbvector(textuser,dbname,user,password,host,port,openai_embeddings_model,typesearch):
    
    conn = get_db_connection(dbname,user,password,host,port)
    cur = conn.cursor()
    print('userprompt')
    print (textuser)
    if  typesearch == "vector":
    
        query = """SELECT
        e.chuncks , e.filename
        FROM data e 
        WHERE e.dvector <=> azure_openai.create_embeddings(%s, %s)::vector < 0.25  
        ORDER BY e.dvector <=> azure_openai.create_embeddings(%s, %s)::vector  
        LIMIT 3;"""
        cur.execute(query, (openai_embeddings_model, textuser, openai_embeddings_model, textuser))
        resutls = str(cur.fetchall())               
        chars = re.escape(string.punctuation)
        res = re.sub('['+chars+']', '',resutls)                        
        
    elif  typesearch == "full text":
        
        
        textuser_escaped = textuser.replace(" ","&").replace("'", "''")
        print(textuser_escaped)
        
        query = """
        SELECT chuncks , filename 
        FROM data 
        WHERE to_tsvector('english',chuncks ) @@ to_tsquery(%s)
        ORDER BY ts_rank_cd(to_tsvector('english', chuncks), to_tsquery(%s)) DESC
        LIMIT 2
        """
        cur.execute(query, (textuser_escaped, textuser_escaped))
        resutls = str(cur.fetchall())               
        chars = re.escape(string.punctuation)
        res = re.sub('['+chars+']', '',resutls)   
        print("fulltext_query")
        print(res)
        
        
        
    elif  typesearch == "hybrid": 
        
        textuser2 = textuser.replace(" ","&").replace("'", "''")
        hybrid_query = """SELECT
        e.chuncks , e.filename
        FROM data e 
        WHERE (e.dvector <=> azure_openai.create_embeddings(%s, %s)::vector < 0.25) 
           OR (to_tsvector('english',chuncks ) @@ to_tsquery(%s))
        ORDER BY e.dvector <=> azure_openai.create_embeddings(%s, %s)::vector  
        LIMIT 1;
        """
               
        cur.execute(hybrid_query, (openai_embeddings_model, textuser, textuser2, openai_embeddings_model, textuser))
        resutls = str(cur.fetchall())               
        chars = re.escape(string.punctuation)
        res = re.sub('['+chars+']', '',resutls)   
        print("hybrid_query")
        print(res)
        
        
        
        
    return res

# Handle chat completion with caching and database integration
def chat_completion(openai_client, system_prompt, user_input, username, dbname, user, password, host, port, openai_embeddings_model, openai_chat_model, typesearch):
    # Query the chat history cache first to see if this question has been asked before
    cache_results = cachesearch(user_input, username, dbname, user, password, host, port, openai_embeddings_model)

    if len(cache_results) > 0:
        return cache_results[0], True
    else:
        # Generate the completion
        completions_results = generatecompletionede(openai_client, system_prompt, user_input, username, dbname, user, password, host, port, openai_embeddings_model, openai_chat_model, typesearch)

        # Cache the response
        cacheresponse(user_input, completions_results, username, dbname, user, password, host, port)

        return completions_results['choices'][0]['message']['content'], False

# Save system prompt to database
def save_system_prompt(username, prompt_name, prompt_text, dbname, user, password, host, port):
    conn = get_db_connection(dbname, user, password, host, port)
    cur = conn.cursor()
    
    # Create table if not exists
    cur.execute('''CREATE TABLE IF NOT EXISTS system_prompts (
                    id serial PRIMARY KEY,
                    username text NOT NULL,
                    prompt_name text NOT NULL,
                    prompt_text text NOT NULL,
                    is_active boolean DEFAULT false,
                    date_added date DEFAULT CURRENT_TIMESTAMP);
                ''')
    
    # Deactivate all other prompts for this user
    cur.execute('UPDATE system_prompts SET is_active = false WHERE username = %s', (username,))
    
    # Insert new prompt as active
    cur.execute('''INSERT INTO system_prompts (username, prompt_name, prompt_text, is_active)
                   VALUES (%s, %s, %s, true)''',
                (username, prompt_name, prompt_text))
    
    conn.commit()
    cur.close()
    conn.close()

# Get active system prompt for user
def get_active_system_prompt(username, dbname, user, password, host, port):
    conn = get_db_connection(dbname, user, password, host, port)
    cur = conn.cursor()
    
    cur.execute('''SELECT prompt_text FROM system_prompts 
                   WHERE username = %s AND is_active = true 
                   ORDER BY date_added DESC LIMIT 1''', (username,))
    
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result:
        return result[0]
    return DEFAULT_SYSTEM_PROMPT

# Get all system prompts for user
def get_all_system_prompts(username, dbname, user, password, host, port):
    """Retrieve all system prompts for a user with their details"""
    conn = get_db_connection(dbname, user, password, host, port)
    cur = conn.cursor()
    
    cur.execute('''SELECT id, prompt_name, prompt_text, is_active, date_added 
                   FROM system_prompts 
                   WHERE username = %s 
                   ORDER BY date_added DESC''', (username,))
    
    prompts = []
    for row in cur.fetchall():
        prompts.append({
            'id': row[0],
            'name': row[1],
            'text': row[2],
            'is_active': row[3],
            'date_added': row[4]
        })
    
    cur.close()
    conn.close()
    return prompts

# Activate a specific prompt
def activate_system_prompt(prompt_id, username, dbname, user, password, host, port):
    """Set a specific prompt as active for the user"""
    conn = get_db_connection(dbname, user, password, host, port)
    cur = conn.cursor()
    
    # Deactivate all prompts for this user
    cur.execute('UPDATE system_prompts SET is_active = false WHERE username = %s', (username,))
    
    # Activate the selected prompt
    cur.execute('UPDATE system_prompts SET is_active = true WHERE id = %s AND username = %s', 
                (prompt_id, username))
    
    conn.commit()
    cur.close()
    conn.close()

# Delete a system prompt
def delete_system_prompt(prompt_id, username, dbname, user, password, host, port):
    """Delete a specific prompt (cannot delete if it's the only one)"""
    conn = get_db_connection(dbname, user, password, host, port)
    cur = conn.cursor()
    
    # Check if it's the last prompt
    cur.execute('SELECT COUNT(*) FROM system_prompts WHERE username = %s', (username,))
    count = cur.fetchone()[0]
    
    if count <= 1:
        cur.close()
        conn.close()
        raise Exception("Cannot delete the last prompt. Create a new one first.")
    
    cur.execute('DELETE FROM system_prompts WHERE id = %s AND username = %s', (prompt_id, username))
    
    conn.commit()
    cur.close()
    conn.close()

# Flask Routes
@app.route('/')
def index():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    return redirect(url_for('chat'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        country = request.form.get('country')
        
        if authenticate(username):
            session['logged_in'] = True
            session['username'] = username
            
            # Get database config from session or use defaults
            dbname = ''.join(filter(str.isalnum, str(config.get('pgdbname', ''))))
            user = ''.join(filter(str.isalnum, str(config.get('pguser', ''))))
            password = ''.join(filter(str.isalnum, str(config.get('pgpassword', ''))))
            host = str(config.get('pghost', '')).replace("'", "").replace("(", "").replace(")", "").replace(",", "")
            port = ''.join(filter(str.isalnum, str(config.get('pgport', ''))))
            
            session['dbname'] = dbname
            session['pguser'] = user
            session['pgpassword'] = password
            session['pghost'] = host
            session['pgport'] = port
            session['openai_endpoint'] = config.get('openai_endpoint', '')
            session['openai_key'] = config.get('openai_key', '')
            session['openai_version'] = config.get('openai_version', '')
            session['openai_chat_model'] = config.get('AZURE_OPENAI_CHAT_MODEL', '')
            session['embeddingssize'] = config.get('embeddingsize', '')
            session['openai_embeddings_model'] = 'text-embedding-ada-002'
            
            try:
                conn = get_db_connection(dbname, user, password, host, port)
                cur = conn.cursor()
                cur.execute('INSERT INTO userapp (username, email, country) VALUES (%s, %s, %s)',
                            (username, email, country))
                conn.commit()
                cur.close()
                conn.close()
            except:
                pass  # User might already exist
            
            flash(f'Welcome {username}!', 'success')
            return redirect(url_for('chat'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/config', methods=['GET', 'POST'])
def config_page():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Save configuration to session
        session['dbname'] = request.form.get('dbname', config.get('pgdbname', ''))
        session['pguser'] = request.form.get('pguser', config.get('pguser', ''))
        session['pgpassword'] = request.form.get('pgpassword', config.get('pgpassword', ''))
        session['pghost'] = request.form.get('pghost', config.get('pghost', ''))
        session['pgport'] = request.form.get('pgport', config.get('pgport', ''))
        session['openai_endpoint'] = request.form.get('openai_endpoint', config.get('openai_endpoint', ''))
        session['openai_key'] = request.form.get('openai_key', config.get('openai_key', ''))
        session['openai_version'] = request.form.get('openai_version', config.get('openai_version', ''))
        session['openai_chat_model'] = request.form.get('openai_chat_model', config.get('AZURE_OPENAI_CHAT_MODEL', ''))
        session['embeddingssize'] = request.form.get('embeddingssize', config.get('embeddingsize', ''))
        session['openai_embeddings_model'] = request.form.get('openai_embeddings_model', 'text-embedding-ada-002')
        
        flash('Configuration saved!', 'success')
    
    return render_template('config.html', config=config, session=session)

@app.route('/initialize', methods=['POST'])
def initialize_db():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'error': 'Not logged in'}), 401
    
    dbname = session.get('dbname', config.get('pgdbname', ''))
    user = session.get('pguser', config.get('pguser', ''))
    password = session.get('pgpassword', config.get('pgpassword', ''))
    host = session.get('pghost', config.get('pghost', ''))
    port = session.get('pgport', config.get('pgport', ''))
    embeddingssize = session.get('embeddingssize', config.get('embeddingsize', ''))
    openai_embeddings_model = session.get('openai_embeddings_model', 'text-embedding-ada-002')
    
    try:
        intialize(dbname, user, password, host, port, embeddingssize, openai_embeddings_model)
        return jsonify({'success': True, 'message': 'Database initialized successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'error': 'Not logged in'}), 401
    
    dbname = session.get('dbname', config.get('pgdbname', ''))
    user = session.get('pguser', config.get('pguser', ''))
    password = session.get('pgpassword', config.get('pgpassword', ''))
    host = session.get('pghost', config.get('pghost', ''))
    port = session.get('pgport', config.get('pgport', ''))
    
    try:
        clearcache(dbname, user, password, host, port)
        return jsonify({'success': True, 'message': 'Cache cleared successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/clear-chat', methods=['POST'])
def clear_chat():
    """Clear all chat history from the session"""
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        # Clear chat history from session
        session['chat_history'] = []
        session.modified = True
        return jsonify({'success': True, 'message': 'Chat history cleared successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/clean-all', methods=['POST'])
def clean_all():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'error': 'Not logged in'}), 401
    
    dbname = session.get('dbname', config.get('pgdbname', ''))
    user = session.get('pguser', config.get('pguser', ''))
    password = session.get('pgpassword', config.get('pgpassword', ''))
    host = session.get('pghost', config.get('pghost', ''))
    port = session.get('pgport', config.get('pgport', ''))
    
    try:
        cleanall(dbname, user, password, host, port)
        return jsonify({'success': True, 'message': 'All tables deleted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Progress tracking dictionary
upload_progress = {}

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            upload_id = str(uuid.uuid4())
            
            # Initialize progress
            upload_progress[upload_id] = {'status': 'uploading', 'progress': 0, 'message': 'Uploading file...'}
            
            # Save file and convert to absolute path
            file.save(filepath)
            filepath = os.path.abspath(filepath)
            
            upload_progress[upload_id] = {'status': 'processing', 'progress': 20, 'message': 'File uploaded, processing...'}
            
            # Debug: Verify file exists
            print(f"File saved to: {filepath}")
            print(f"File exists: {os.path.exists(filepath)}")
            print(f"File size: {os.path.getsize(filepath)} bytes")
            
            dbname = session.get('dbname', config.get('pgdbname', ''))
            user = session.get('pguser', config.get('pguser', ''))
            password = session.get('pgpassword', config.get('pgpassword', ''))
            host = session.get('pghost', config.get('pghost', ''))
            port = session.get('pgport', config.get('pgport', ''))
            
            try:
                name = os.path.splitext(filename)[0]
                
                # Verify file exists before processing
                if not os.path.exists(filepath):
                    raise FileNotFoundError(f"File not found at: {filepath}")
                
                upload_progress[upload_id] = {'status': 'processing', 'progress': 40, 'message': 'Loading and splitting document...'}
                
                if filename.endswith('.pdf'):
                    loadpdffile(name, filepath, dbname, user, password, host, port, upload_id)
                elif filename.endswith(('.doc', '.docx')):
                    loadwordfile(name, filepath, dbname, user, password, host, port, upload_id)
                elif filename.endswith(('.ppt', '.pptx')):
                    loadpptfile(name, filepath, dbname, user, password, host, port, upload_id)
                elif filename.endswith(('.xls', '.xlsx')):
                    loadxlsfile(name, filepath, dbname, user, password, host, port, upload_id)
                elif filename.endswith('.csv'):
                    loadcsvfile(name, filepath, dbname, user, password, host, port, upload_id)
                elif filename.endswith('.json'):
                    loadjsonfile(name, filepath, dbname, user, password, host, port, upload_id)
                else:
                    upload_progress[upload_id] = {'status': 'error', 'progress': 0, 'message': 'Unsupported file type'}
                    os.remove(filepath)
                    return jsonify({'error': 'Unsupported file type', 'upload_id': upload_id}), 400
                
                os.remove(filepath)
                upload_progress[upload_id] = {'status': 'complete', 'progress': 100, 'message': f'File {filename} loaded successfully!'}
                return jsonify({'success': True, 'upload_id': upload_id, 'message': f'File {filename} loaded successfully!'}), 200
                
            except FileNotFoundError as e:
                upload_progress[upload_id] = {'status': 'error', 'progress': 0, 'message': f'File not found: {str(e)}'}
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({'error': f'File not found: {str(e)}', 'upload_id': upload_id}), 500
            except Exception as e:
                import traceback
                error_msg = f'Error loading file: {str(e)}'
                print(f"{error_msg}\n\nDetails: {traceback.format_exc()}")
                upload_progress[upload_id] = {'status': 'error', 'progress': 0, 'message': error_msg}
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({'error': error_msg, 'upload_id': upload_id}), 500
    
    return render_template('upload.html')

@app.route('/upload-progress/<upload_id>')
def upload_progress_status(upload_id):
    """Return the current progress of an upload"""
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'error': 'Unauthorized'}), 401
    
    progress = upload_progress.get(upload_id, {'status': 'unknown', 'progress': 0, 'message': 'Unknown upload'})
    return jsonify(progress)

@app.route('/chat', methods=['GET'])
def chat():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    username = session['username']
    
    # Initialize chat history in session
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    return render_template('chat.html', username=username, chat_history=session.get('chat_history', []))

@app.route('/send-message', methods=['POST'])
def send_message():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    user_input = data.get('message', '')
    typesearch = data.get('search_type', 'vector')
    
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400
    
    username = session['username']
    
    # Get database config
    dbname = session.get('dbname', config.get('pgdbname', ''))
    user = session.get('pguser', config.get('pguser', ''))
    password = session.get('pgpassword', config.get('pgpassword', ''))
    host = session.get('pghost', config.get('pghost', ''))
    port = session.get('pgport', config.get('pgport', ''))
    openai_endpoint = session.get('openai_endpoint', config.get('openai_endpoint', ''))
    openai_key = session.get('openai_key', config.get('openai_key', ''))
    openai_version = session.get('openai_version', config.get('openai_version', ''))
    openai_chat_model = session.get('openai_chat_model', config.get('AZURE_OPENAI_CHAT_MODEL', ''))
    openai_embeddings_model = session.get('openai_embeddings_model', 'text-embedding-ada-002')
    
    # Get system prompt (from database or use default)
    system_prompt = get_active_system_prompt(username, dbname, user, password, host, port)
    system_prompt = system_prompt.replace("{username}", username)
    
    # Create OpenAI client
    openai_client = AzureOpenAI(
        api_key=openai_key,
        api_version=openai_version,
        azure_endpoint=openai_endpoint
    )
    
    try:
        start_time = time.time()
        response_payload, cached = chat_completion(
            openai_client, system_prompt, user_input, username,
            dbname, user, password, host, port,
            openai_embeddings_model, openai_chat_model, typesearch
        )
        end_time = time.time()
        elapsed_time = round((end_time - start_time) * 1000, 2)
        
        if cached:
            response = str(response_payload[0])
        else:
            response = response_payload
        
        # Add to chat history
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        session['chat_history'].append({
            'user': user_input,
            'assistant': response,
            'time': elapsed_time,
            'cached': cached
        })
        session.modified = True
        
        return jsonify({
            'success': True,
            'response': response,
            'time': elapsed_time,
            'cached': cached
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/system-prompt', methods=['GET', 'POST'])
def system_prompt():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    username = session['username']
    
    dbname = session.get('dbname', config.get('pgdbname', ''))
    user = session.get('pguser', config.get('pguser', ''))
    password = session.get('pgpassword', config.get('pgpassword', ''))
    host = session.get('pghost', config.get('pghost', ''))
    port = session.get('pgport', config.get('pgport', ''))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'save':
            prompt_name = request.form.get('prompt_name', 'Custom Prompt')
            prompt_text = request.form.get('prompt_text', DEFAULT_SYSTEM_PROMPT)
            
            try:
                save_system_prompt(username, prompt_name, prompt_text, dbname, user, password, host, port)
                flash('System prompt saved successfully!', 'success')
            except Exception as e:
                flash(f'Error saving prompt: {str(e)}', 'error')
        
        elif action == 'reset':
            try:
                save_system_prompt(username, 'Default Prompt', DEFAULT_SYSTEM_PROMPT, dbname, user, password, host, port)
                flash('System prompt reset to default!', 'success')
            except Exception as e:
                flash(f'Error resetting prompt: {str(e)}', 'error')
        
        elif action == 'activate':
            prompt_id = request.form.get('prompt_id')
            try:
                activate_system_prompt(prompt_id, username, dbname, user, password, host, port)
                flash('Prompt activated successfully!', 'success')
            except Exception as e:
                flash(f'Error activating prompt: {str(e)}', 'error')
        
        elif action == 'delete':
            prompt_id = request.form.get('prompt_id')
            try:
                delete_system_prompt(prompt_id, username, dbname, user, password, host, port)
                flash('Prompt deleted successfully!', 'success')
            except Exception as e:
                flash(f'Error deleting prompt: {str(e)}', 'error')
    
    # Get current active prompt
    current_prompt = get_active_system_prompt(username, dbname, user, password, host, port)
    
    # Get all prompts for this user
    all_prompts = get_all_system_prompts(username, dbname, user, password, host, port)
    
    # Get preview with username replaced
    preview_prompt = current_prompt.replace("{username}", username)
    
    return render_template('system_prompt.html', 
                         current_prompt=current_prompt, 
                         preview_prompt=preview_prompt,
                         default_prompt=DEFAULT_SYSTEM_PROMPT,
                         all_prompts=all_prompts,
                         username=username)

@app.route('/files', methods=['GET'])
def list_files():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    dbname = session.get('dbname', config.get('pgdbname', ''))
    user = session.get('pguser', config.get('pguser', ''))
    password = session.get('pgpassword', config.get('pgpassword', ''))
    host = session.get('pghost', config.get('pghost', ''))
    port = session.get('pgport', config.get('pgport', ''))
    
    try:
        conn = get_db_connection(dbname, user, password, host, port)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT filename FROM data ORDER BY filename")
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        files = [row[0] for row in results]
        
        return render_template('files.html', files=files)
        
    except Exception as e:
        flash(f'Error loading files: {str(e)}', 'error')
        return render_template('files.html', files=[])

@app.route('/argus', methods=['GET', 'POST'])
def argus():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        argusdb = request.form.get('argusdb', 'doc-extracts')
        argusurl = request.form.get('argusurl', '')
        arguskey = request.form.get('arguskey', '')
        arguscollection = request.form.get('arguscollection', 'documents')
        
        if not argusurl or not arguskey:
            flash('Please provide Argus URL and Key', 'error')
            return redirect(request.url)
        
        dbname = session.get('dbname', config.get('pgdbname', ''))
        user = session.get('pguser', config.get('pguser', ''))
        password = session.get('pgpassword', config.get('pgpassword', ''))
        host = session.get('pghost', config.get('pghost', ''))
        port = session.get('pgport', config.get('pgport', ''))
        
        try:
            total = loaddataargus(argusdb, arguscollection, argusurl, arguskey, 
                                 dbname, user, password, host, port)
            flash(f'Successfully loaded {total} records from Argus Accelerator!', 'success')
        except Exception as e:
            flash(f'Error loading from Argus: {str(e)}', 'error')
    
    return render_template('argus.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)


