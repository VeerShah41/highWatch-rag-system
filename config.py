import os
from dotenv import load_dotenv

load_dotenv()

# ── Google OAuth ──────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")

# ── LLM ───────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # "groq" or "gemini"

# ── Storage ───────────────────────────────────────────────────────────────────
STORAGE_DIR = os.getenv("STORAGE_DIR", "./storage")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./downloads")

# Create directories if they don't exist
os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ── Derived paths ─────────────────────────────────────────────────────────────
FAISS_INDEX_PATH = os.path.join(STORAGE_DIR, "faiss_index.bin")
METADATA_PATH = os.path.join(STORAGE_DIR, "faiss_metadata.json")
TOKENS_PATH = os.path.join(STORAGE_DIR, "tokens.json")
PROCESSED_FILES_PATH = os.path.join(STORAGE_DIR, "processed_files.json")

# ── Google OAuth Scopes ───────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]
