import os
from dotenv import load_dotenv

load_dotenv()

# ── Google OAuth ──────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Automatically detect Render's live URL, otherwise use env var or localhost
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
if RENDER_EXTERNAL_URL:
    GOOGLE_REDIRECT_URI = f"{RENDER_EXTERNAL_URL}/auth/callback"
else:
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

from context import user_id_ctx

def get_user_dir() -> str:
    user_id = user_id_ctx.get()
    user_dir = os.path.join(STORAGE_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def get_faiss_index_path() -> str:
    return os.path.join(get_user_dir(), "faiss_index.bin")

def get_metadata_path() -> str:
    return os.path.join(get_user_dir(), "faiss_metadata.json")

def get_tokens_path() -> str:
    return os.path.join(get_user_dir(), "tokens.json")

def get_processed_files_path() -> str:
    return os.path.join(get_user_dir(), "processed_files.json")


# ── Google OAuth Scopes ───────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]
