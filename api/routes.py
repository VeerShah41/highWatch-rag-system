import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from connectors.google_drive import (
    get_auth_url,
    exchange_code_for_tokens,
    get_drive_files,
    download_file,
    is_drive_connected,
)
from processing.extractor import extract_text
from processing.chunker import chunk_text
from embedding.embedder import get_embeddings, get_single_embedding
from search.vector_store import add_chunks, search, get_index_stats
from llm.answer import generate_answer
from config import PROCESSED_FILES_PATH, FAISS_INDEX_PATH

router = APIRouter()


# ── Request/Response Models ───────────────────────────────────────────────────

class AskRequest(BaseModel):
    query: str


# ── Auth Routes ───────────────────────────────────────────────────────────────

@router.get("/auth/login", tags=["Auth"])
def auth_login():
    """Redirect user to Google OAuth consent screen."""
    auth_url = get_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/auth/callback", tags=["Auth"])
def auth_callback(code: str):
    """Handle Google OAuth callback and store tokens."""
    try:
        exchange_code_for_tokens(code)
        return RedirectResponse(url="/")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")


# ── Sync Drive ────────────────────────────────────────────────────────────────

@router.post("/sync-drive", tags=["Sync"])
def sync_drive():
    """
    Fetch all PDF/Docs/TXT files from Google Drive, process them,
    and index them into FAISS. Supports incremental sync.
    """
    if not is_drive_connected():
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please visit /auth/login first.",
        )

    # Load incremental sync manifest
    processed_files: dict = {}
    if os.path.exists(PROCESSED_FILES_PATH):
        with open(PROCESSED_FILES_PATH, "r") as f:
            processed_files = json.load(f)

    # Fetch all eligible files from Drive
    try:
        drive_files = get_drive_files()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Google Drive error: {str(e)}")

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
            # 1. Download
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
    with open(PROCESSED_FILES_PATH, "w") as f:
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
def ask_question(body: AskRequest):
    """
    Answer a natural language question using RAG over indexed documents.
    """
    if not os.path.exists(FAISS_INDEX_PATH):
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


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/status", tags=["Health"])
def status():
    """Return current system status — auth, index stats."""
    stats = get_index_stats()
    return {
        **stats,
        "drive_connected": is_drive_connected(),
    }
