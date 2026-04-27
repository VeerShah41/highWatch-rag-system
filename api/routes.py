import os
import json
import uuid
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from connectors.google_drive import (
    get_auth_url,
    exchange_code_for_tokens,
    get_drive_files,
    download_file,
    is_drive_connected,
    get_user_email,
)
from processing.extractor import extract_text
from processing.chunker import chunk_text
from embedding.embedder import get_embeddings, get_single_embedding
from search.vector_store import add_chunks, search, get_index_stats, get_sample_chunks
from llm.answer import generate_answer, generate_recommendations
from config import get_processed_files_path, get_faiss_index_path
from context import user_id_ctx

router = APIRouter()

# ── Dependency for Multi-User ────────────────────────────────────────────────
async def get_user_id(request: Request, response: Response):
    user_id = request.cookies.get("hw_user_id")
    if not user_id:
        user_id = str(uuid.uuid4())
        response.set_cookie(key="hw_user_id", value=user_id, max_age=86400 * 30)
    user_id_ctx.set(user_id)
    return user_id

# ── Request/Response Models ───────────────────────────────────────────────────

class AskRequest(BaseModel):
    query: str


class SyncRequest(BaseModel):
    folder_id: str | None = None


# ── Auth Routes ───────────────────────────────────────────────────────────────

@router.get("/auth/login", tags=["Auth"])
def auth_login(user_id: str = Depends(get_user_id)):
    """Redirect user to Google OAuth consent screen."""
    auth_url = get_auth_url()
    res = RedirectResponse(url=auth_url)
    res.set_cookie(key="hw_user_id", value=user_id, max_age=86400 * 30)
    return res


@router.get("/auth/callback", tags=["Auth"])
def auth_callback(code: str, user_id: str = Depends(get_user_id)):
    """Handle Google OAuth callback and store tokens."""
    try:
        exchange_code_for_tokens(code)
        res = RedirectResponse(url="/")
        res.set_cookie(key="hw_user_id", value=user_id, max_age=86400 * 30)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")


# ── Sync Drive ────────────────────────────────────────────────────────────────

@router.post("/sync-drive", tags=["Sync"])
def sync_drive(body: SyncRequest = SyncRequest(), user_id: str = Depends(get_user_id)):
    """
    Fetch PDF/TXT files from Google Drive (optionally from a specific folder), 
    process them, and index them into FAISS. Supports incremental sync.
    """
    # Bypass Auth if a public folder_id is provided
    if not body.folder_id and not is_drive_connected():
        raise HTTPException(
            status_code=401,
            detail="Drive not connected. Please authenticate first or provide a public folder link."
        )

    # Load incremental sync manifest
    processed_files: dict = {}
    if os.path.exists(get_processed_files_path()):
        with open(get_processed_files_path(), "r") as f:
            processed_files = json.load(f)

    # Fetch files
    try:
        if body.folder_id and not is_drive_connected():
            # Anonymous public folder download using gdown
            import gdown
            from config import DOWNLOAD_DIR
            
            folder_url = f"https://drive.google.com/drive/folders/{body.folder_id}"
            out_dir = os.path.join(DOWNLOAD_DIR, body.folder_id)
            os.makedirs(out_dir, exist_ok=True)
            
            # download_folder returns a list of downloaded file paths
            downloaded_files = gdown.download_folder(url=folder_url, output=out_dir, quiet=True, use_cookies=False)
            
            if not downloaded_files:
                raise HTTPException(status_code=400, detail="Folder is empty, invalid, or not publicly accessible.")
                
            drive_files = []
            for filepath in downloaded_files:
                if filepath.lower().endswith('.pdf') or filepath.lower().endswith('.txt'):
                    drive_files.append({
                        "id": filepath,  # Use local path as ID
                        "name": os.path.basename(filepath),
                        "mimeType": "application/pdf" if filepath.lower().endswith('.pdf') else "text/plain",
                        "modifiedTime": "public_folder_sync"
                    })
        else:
            # Normal authenticated fetch
            drive_files = get_drive_files(folder_id=body.folder_id)
            
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Drive fetch error: {str(e)}")

    files_processed = []
    total_chunks = 0
    skipped = 0

    for file in drive_files:
        file_id = file["id"]
        file_name = file["name"]
        mime_type = file["mimeType"]
        modified_time = file.get("modifiedTime", "")

        # ── Incremental sync: skip if already processed and unchanged ──
        if file_id in processed_files and processed_files[file_id] == modified_time:
            print(f"[Sync] Skipping unchanged file: {file_name}")
            skipped += 1
            continue

        print(f"[Sync] Processing: {file_name}")

        try:
            # Download file (or use already downloaded path from gdown)
            if os.path.exists(file_id):
                local_path = file_id
            else:
                local_path = download_file(file_id, file_name, mime_type)

            # 2. Extract text
            text = extract_text(local_path, mime_type)
            if not text.strip():
                print(f"[Sync] No text extracted from {file_name}, skipping.")
                continue

            # 3. Chunk
            chunks = chunk_text(text, file_name, file_id)
            if not chunks:
                continue

            # 4. Embed
            texts = [c["chunk_text"] for c in chunks]
            embeddings = get_embeddings(texts)

            # 5. Store in FAISS
            add_chunks(chunks, embeddings)

            total_chunks += len(chunks)
            files_processed.append(file_name)

            # Update incremental sync manifest
            processed_files[file_id] = modified_time

        except Exception as e:
            print(f"[Sync] Error processing {file_name}: {e}")
            continue

    # Save updated manifest
    with open(get_processed_files_path(), "w") as f:
        json.dump(processed_files, f, indent=2)

    return {
        "status": "success",
        "files_processed": len(files_processed),
        "files_skipped_unchanged": skipped,
        "total_new_chunks": total_chunks,
        "files": files_processed,
    }


# ── Ask Question ──────────────────────────────────────────────────────────────

@router.post("/ask", tags=["RAG"])
def ask_question(body: AskRequest, user_id: str = Depends(get_user_id)):
    """
    Answer a natural language question using RAG over indexed documents.
    """
    if not os.path.exists(get_faiss_index_path()):
        raise HTTPException(
            status_code=400,
            detail="No documents indexed yet. Please call POST /sync-drive first.",
        )

    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="Query cannot be empty.")

    try:
        # 1. Embed the query
        query_embedding = get_single_embedding(query)

        # 2. Retrieve top relevant chunks from FAISS
        top_chunks = search(query_embedding, top_k=5)

        # 3. Generate grounded answer via LLM
        result = generate_answer(query, top_chunks)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG error: {str(e)}")


@router.get("/recommend-questions", tags=["RAG"])
def recommend_questions(user_id: str = Depends(get_user_id)):
    """
    Generate 3 suggested questions grounded in the indexed document context.
    """
    try:
        # Get a few sample chunks for context
        samples = get_sample_chunks(n=5)
        questions = generate_recommendations(samples)
        return {"questions": questions}
    except Exception as e:
        # Return defaults on failure
        return {"questions": [
            "What is our refund policy?",
            "Summarize IT security SOP",
            "What are the compliance guidelines?"
        ]}


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/status", tags=["Health"])
def status(user_id: str = Depends(get_user_id)):
    """Return current system status — auth, index stats."""
    stats = get_index_stats()
    return {
        **stats,
        "drive_connected": is_drive_connected(),
        "user_email": get_user_email(),
    }


# ── System Maintenance ────────────────────────────────────────────────────────

@router.post("/disconnect", tags=["System"])
def disconnect_drive(user_id: str = Depends(get_user_id)):
    """Disconnect Google Drive by removing OAuth tokens."""
    import os
    from config import get_tokens_path
    
    if os.path.exists(get_tokens_path()):
        os.remove(get_tokens_path())
        
    return {"status": "success", "message": "Drive disconnected successfully."}

@router.post("/clear-data", tags=["System"])
def clear_data(user_id: str = Depends(get_user_id)):
    """Clear all indexed FAISS data and downloaded files."""
    import shutil
    import os
    from config import STORAGE_DIR, DOWNLOAD_DIR
    from search.vector_store import _load_index
    
    # We must reset the in-memory global FAISS index and metadata
    import search.vector_store
    search.vector_store.index = None
    search.vector_store.metadata = {}
    
    # Clear storage and downloads directories
    if os.path.exists(STORAGE_DIR):
        shutil.rmtree(STORAGE_DIR)
        os.makedirs(STORAGE_DIR, exist_ok=True)
        
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        
    return {"status": "success", "message": "Synced data cleared successfully."}
