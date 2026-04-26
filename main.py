from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.routes import router

app = FastAPI(
    title="Highwatch AI — RAG System",
    description=(
        "A Retrieval-Augmented Generation (RAG) API that connects to Google Drive, "
        "processes documents, and answers questions grounded in your own files."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins for local dev / demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routes
app.include_router(router)

# Serve frontend
import os
os.makedirs("frontend", exist_ok=True)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve demo docs
os.makedirs("demo_docs", exist_ok=True)
app.mount("/demo_docs", StaticFiles(directory="demo_docs"), name="demo_docs")

@app.get("/", tags=["Frontend"])
def serve_frontend():
    return FileResponse("frontend/index.html")

if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
