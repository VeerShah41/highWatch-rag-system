# PROJECT SPECIFICATION — Highwatch AI RAG System
# AI Platform Engineer Trial Assignment

---

## OVERVIEW

You are building a **Retrieval-Augmented Generation (RAG) system** that:
1. Connects to a user's **Google Drive** via OAuth 2.0
2. Fetches and processes documents (PDF, Google Docs, TXT)
3. Chunks and embeds the documents into a vector database (FAISS)
4. Answers natural language questions grounded in those documents using an LLM
5. Returns answers with source citations

This is essentially a **"ChatGPT over your Google Drive"** — but built from scratch as a backend API using Python + FastAPI.

---

## TECH STACK (MUST FOLLOW EXACTLY)

| Layer | Technology | Notes |
|---|---|---|
| API Framework | FastAPI (Python) | All endpoints here |
| Google Drive Auth | OAuth 2.0 (google-auth, google-api-python-client) | User-facing login flow |
| PDF Parsing | PyMuPDF (fitz) | Fast, reliable |
| Google Docs Parsing | google-api-python-client (export to plain text) | Use Drive API export |
| TXT Parsing | Native Python read | Simple |
| Text Chunking | LangChain's RecursiveCharacterTextSplitter | chunk_size=512, overlap=50 |
| Embedding Model | sentence-transformers (all-MiniLM-L6-v2) | Local, free, fast |
| Vector Store | FAISS (faiss-cpu) | Store + retrieve embeddings |
| LLM | Groq API (llama3-70b-8192) OR Google Gemini | Answer generation |
| Metadata Store | JSON file (faiss_metadata.json) | Maps chunk index to doc info |
| Containerization | Docker + docker-compose | Bonus, but include |
| Environment Config | python-dotenv (.env file) | All secrets here |

---

## FOLDER STRUCTURE (MUST FOLLOW EXACTLY)

```
highminds/
│
├── api/
│   ├── __init__.py
│   └── routes.py                  # All FastAPI route definitions
│
├── connectors/
│   ├── __init__.py
│   └── google_drive.py            # OAuth flow + Drive file fetching
│
├── processing/
│   ├── __init__.py
│   ├── extractor.py               # Extract raw text from PDF/Docs/TXT
│   └── chunker.py                 # Split text into chunks with metadata
│
├── embedding/
│   ├── __init__.py
│   └── embedder.py                # Generate embeddings using SentenceTransformers
│
├── search/
│   ├── __init__.py
│   └── vector_store.py            # FAISS index: save, load, search
│
├── llm/
│   ├── __init__.py
│   └── answer.py                  # Call LLM with context + query, return answer + sources
│
├── storage/
│   ├── faiss_index.bin            # FAISS binary index (auto-generated)
│   └── faiss_metadata.json        # Chunk metadata (auto-generated)
│
├── downloads/                     # Temp folder for downloaded Drive files
│
├── main.py                        # FastAPI app entry point
├── config.py                      # Load all env vars using python-dotenv
├── requirements.txt               # All dependencies
├── Dockerfile                     # Docker build file
├── docker-compose.yml             # Docker compose config
├── .env                           # Secret keys (NOT committed to git)
├── .env.example                   # Template for .env
├── .gitignore
├── README.md
└── PROJECT_SPEC.md                # This file
```

---

## ENVIRONMENT VARIABLES (.env)

```env
# Google OAuth Credentials (from Google Cloud Console)
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# LLM Provider — choose one
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Active LLM Provider: "groq" or "gemini"
LLM_PROVIDER=groq

# App Config
PORT=8000
STORAGE_DIR=./storage
DOWNLOAD_DIR=./downloads
```

---

## MODULE-BY-MODULE SPECIFICATION

---

### MODULE 1: `config.py`

**Purpose:** Centralized configuration loader. All other modules import from here.

```python
# config.py
# Load environment variables from .env
# Expose: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI,
#         GROQ_API_KEY, GEMINI_API_KEY, LLM_PROVIDER, STORAGE_DIR, DOWNLOAD_DIR
# Create STORAGE_DIR and DOWNLOAD_DIR directories if they don't exist
```

---

### MODULE 2: `connectors/google_drive.py`

**Purpose:** Handle Google OAuth 2.0 flow and fetch files from Drive.

#### OAuth Flow:
1. `GET /auth/login` → Redirect user to Google consent screen
2. Google redirects back to `GET /auth/callback?code=...`
3. Exchange code for access + refresh tokens
4. Store tokens in memory (or a JSON file `storage/tokens.json`) per user session

#### File Fetching Logic (called by `/sync-drive`):
1. Use the stored OAuth token to authenticate
2. Call Drive API: list files where `mimeType` is:
   - `application/pdf`
   - `application/vnd.google-apps.document` (Google Docs)
   - `text/plain`
3. For PDFs and TXTs: download the file binary to `downloads/` folder
4. For Google Docs: export as `text/plain` using Drive API export endpoint
5. Return a list of file objects: `[{ id, name, mimeType, localPath }]`

#### Key Functions:
```python
def get_auth_url() -> str:
    # Returns the Google OAuth consent URL

def exchange_code_for_tokens(code: str) -> dict:
    # Exchanges auth code for access_token + refresh_token
    # Saves tokens to storage/tokens.json
    # Returns token dict

def get_drive_files(token: dict) -> list[dict]:
    # Lists all PDF/Doc/TXT files from user's Drive
    # Returns list of {id, name, mimeType}

def download_file(token: dict, file_id: str, file_name: str, mime_type: str) -> str:
    # Downloads file to downloads/ directory
    # For Google Docs: export as plain text
    # Returns local file path
```

---

### MODULE 3: `processing/extractor.py`

**Purpose:** Extract raw text from downloaded files.

```python
def extract_text(file_path: str, mime_type: str) -> str:
    # If mime_type == "application/pdf": use PyMuPDF (fitz)
    # If mime_type == "text/plain" or Google Doc exported as txt: read file directly
    # Clean the text: remove extra whitespace, normalize newlines
    # Return cleaned text string
```

**PDF Extraction (PyMuPDF):**
```python
import fitz  # PyMuPDF
doc = fitz.open(file_path)
text = ""
for page in doc:
    text += page.get_text()
```

**Text Cleaning:**
- Strip leading/trailing whitespace
- Replace multiple newlines with single newline
- Remove null bytes or special characters

---

### MODULE 4: `processing/chunker.py`

**Purpose:** Split extracted text into overlapping chunks with metadata.

```python
def chunk_text(text: str, file_name: str, file_id: str, source: str = "gdrive") -> list[dict]:
    # Use RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    # Return list of chunks, each with:
    # {
    #   "chunk_text": "...",
    #   "doc_id": file_id,
    #   "file_name": file_name,
    #   "source": "gdrive",
    #   "chunk_index": 0  # position within the document
    # }
```

**Chunking Strategy:**
- `chunk_size = 512` characters
- `chunk_overlap = 50` characters (ensures context continuity between chunks)
- Use `RecursiveCharacterTextSplitter` from `langchain.text_splitter`
- This splits on: `["\n\n", "\n", " ", ""]` in order (respects paragraphs first)

---

### MODULE 5: `embedding/embedder.py`

**Purpose:** Convert text chunks into vector embeddings.

```python
# Use: sentence-transformers model "all-MiniLM-L6-v2"
# This model produces 384-dimensional float32 vectors
# Load the model once at module level (singleton pattern)

def get_embeddings(texts: list[str]) -> np.ndarray:
    # Takes a list of strings
    # Returns numpy array of shape (len(texts), 384)
    # Use model.encode(texts, batch_size=32, show_progress_bar=False)
    # Return as float32 numpy array

def get_single_embedding(text: str) -> np.ndarray:
    # Returns embedding for a single text string
    # Shape: (384,) float32
```

---

### MODULE 6: `search/vector_store.py`

**Purpose:** Manage the FAISS index — add, save, load, and search.

```python
FAISS_INDEX_PATH = "storage/faiss_index.bin"
METADATA_PATH = "storage/faiss_metadata.json"

# The metadata file maps integer index → chunk dict
# Example: { "0": { chunk_text, doc_id, file_name, source, chunk_index }, "1": {...}, ... }

def add_chunks(chunks: list[dict], embeddings: np.ndarray):
    # Load existing FAISS index if it exists, else create new IndexFlatL2(384)
    # Add the new embeddings to the index
    # Append the chunk metadata to faiss_metadata.json
    # Save the updated index to faiss_index.bin
    # IMPORTANT: Track global offset so metadata keys are always unique

def search(query_embedding: np.ndarray, top_k: int = 5) -> list[dict]:
    # Load FAISS index from faiss_index.bin
    # Load metadata from faiss_metadata.json
    # Run index.search(query_embedding, top_k)
    # Return the top_k chunk metadata dicts (with chunk_text and file_name)

def save_index(index):
    # Save FAISS index using faiss.write_index()

def load_index():
    # Load FAISS index using faiss.read_index()
    # Return None if file doesn't exist
```

---

### MODULE 7: `llm/answer.py`

**Purpose:** Call the LLM with retrieved context and generate a grounded answer.

```python
def generate_answer(query: str, context_chunks: list[dict]) -> dict:
    # Build a prompt using the context chunks
    # Call the LLM (Groq or Gemini based on LLM_PROVIDER env var)
    # Return: { "answer": str, "sources": list[str] }
```

**Prompt Template:**
```
You are a helpful AI assistant. Answer the user's question based ONLY on the provided context documents.
If the answer is not in the context, say "I don't have enough information in the provided documents to answer this."

Context:
---
[Chunk 1 from file_name_1]
chunk_text_1

[Chunk 2 from file_name_2]
chunk_text_2
...
---

User Question: {query}

Answer:
```

**Groq API Call:**
```python
from groq import Groq
client = Groq(api_key=GROQ_API_KEY)
response = client.chat.completions.create(
    model="llama3-70b-8192",
    messages=[{"role": "user", "content": prompt}]
)
answer = response.choices[0].message.content
```

**Gemini API Call (alternative):**
```python
import google.generativeai as genai
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content(prompt)
answer = response.text
```

**Sources extraction:**
- Collect unique `file_name` values from the returned context chunks
- Return as a deduplicated list

---

### MODULE 8: `api/routes.py`

**Purpose:** All FastAPI route definitions.

#### Routes:

**`GET /`**
- Returns: `{ "status": "ok", "message": "Highwatch AI RAG API is running" }`

**`GET /auth/login`**
- Redirects user to Google OAuth consent URL
- Uses `get_auth_url()` from `connectors/google_drive.py`

**`GET /auth/callback?code=...`**
- Receives OAuth code from Google
- Calls `exchange_code_for_tokens(code)`
- Stores tokens
- Returns: `{ "status": "authenticated", "message": "Google Drive connected successfully" }`

**`POST /sync-drive`**
- Loads stored OAuth token
- Calls `get_drive_files(token)` → fetches all eligible files
- For each file:
  1. Downloads it via `download_file()`
  2. Extracts text via `extract_text()`
  3. Chunks it via `chunk_text()`
  4. Generates embeddings via `get_embeddings()`
  5. Stores in FAISS via `add_chunks()`
- Returns:
```json
{
  "status": "success",
  "files_processed": 5,
  "total_chunks": 142,
  "files": ["policy.pdf", "sop.docx", "guidelines.txt"]
}
```

**`POST /ask`**
- Request body: `{ "query": "What is our refund policy?" }`
- Steps:
  1. Generate query embedding via `get_single_embedding(query)`
  2. Search FAISS index for top 5 relevant chunks
  3. Call `generate_answer(query, chunks)`
- Returns:
```json
{
  "answer": "The refund policy states that...",
  "sources": ["policy.pdf", "guidelines.txt"],
  "chunks_used": 5
}
```

**`GET /status`**
- Returns current system status:
```json
{
  "faiss_index_exists": true,
  "total_chunks_indexed": 142,
  "drive_connected": true
}
```

---

### MODULE 9: `main.py`

**Purpose:** FastAPI app entry point.

```python
from fastapi import FastAPI
from api.routes import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Highwatch AI RAG System",
    description="ChatGPT over your Google Drive",
    version="1.0.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

---

## COMPLETE DATA FLOW

```
USER → GET /auth/login
  → Redirect to Google OAuth
  → User grants permission
  → Google → GET /auth/callback?code=XYZ
  → Tokens stored in storage/tokens.json

USER → POST /sync-drive
  → Load tokens
  → Drive API: list files (PDF, Docs, TXT)
  → For each file:
      download → extract text → chunk → embed → store in FAISS
  → Return summary

USER → POST /ask { "query": "What is the refund policy?" }
  → Embed query
  → FAISS search → top 5 chunks
  → Build prompt with context
  → LLM call → answer
  → Return { answer, sources }
```

---

## REQUIREMENTS.TXT

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-dotenv==1.0.1
google-auth==2.29.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.126.0
PyMuPDF==1.24.2
langchain==0.2.0
langchain-text-splitters==0.2.0
sentence-transformers==3.0.0
faiss-cpu==1.8.0
numpy==1.26.4
groq==0.9.0
google-generativeai==0.7.0
requests==2.31.0
```

---

## DOCKER SETUP

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p storage downloads
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: "3.9"
services:
  rag-api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./storage:/app/storage
      - ./downloads:/app/downloads
```

---

## ERROR HANDLING RULES

- If Drive token is missing when `/sync-drive` is called → return 401 with message "Please authenticate first via /auth/login"
- If FAISS index doesn't exist when `/ask` is called → return 400 with message "No documents indexed yet. Please run /sync-drive first"
- If Drive API fails → return 503 with error detail
- If LLM API fails → return 500 with error detail
- All endpoints should return errors in format: `{ "error": "message here" }`

---

## INCREMENTAL SYNC (EXCEPTIONAL TIER — IMPLEMENT IF TIME ALLOWS)

- Maintain a `storage/processed_files.json` that stores `{ file_id: last_modified_time }`
- During `/sync-drive`, for each Drive file:
  - Check its `modifiedTime` from Drive API
  - If `file_id` not in `processed_files.json` OR `modifiedTime` is newer → process it
  - Else → skip (already up to date)
- This avoids re-processing unchanged documents

---

## EVALUATION CHECKLIST

### Must Have ✅
- [ ] Google OAuth flow works (auth/login → auth/callback)
- [ ] `/sync-drive` fetches and processes Drive documents
- [ ] `/ask` returns relevant answers with sources

### Strong Candidate ✅
- [ ] RecursiveCharacterTextSplitter with overlap used
- [ ] Answers are grounded (only from documents)
- [ ] Clean, consistent API responses

### Exceptional ✅
- [ ] Incremental sync (skip already-processed files)
- [ ] `/status` endpoint with metadata stats
- [ ] Docker + docker-compose included
- [ ] README with clear setup guide
- [ ] Sample test queries documented

---

## SAMPLE TEST SCENARIO

1. Upload `refund_policy.pdf` and `employee_handbook.pdf` to your Google Drive
2. Start the app and visit `http://localhost:8000/auth/login` to authenticate
3. Call `POST /sync-drive` → system processes both PDFs
4. Call `POST /ask` with:
```json
{ "query": "What is the refund policy for damaged items?" }
```
5. Expected response:
```json
{
  "answer": "According to the refund policy document, damaged items can be returned within 30 days...",
  "sources": ["refund_policy.pdf"],
  "chunks_used": 5
}
```

---

*This specification is complete and self-contained. Any LLM reading this document has all information needed to implement the full system without further clarification.*
