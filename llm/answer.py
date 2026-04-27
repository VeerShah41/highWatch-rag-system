from groq import Groq
from config import GROQ_API_KEY, GEMINI_API_KEY, LLM_PROVIDER


def _build_prompt(query: str, context_chunks: list[dict]) -> str:
    """Build a grounded prompt using retrieved context chunks."""
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        file_name = chunk.get("file_name", "Unknown Document")
        chunk_text = chunk.get("chunk_text", "")
        context_parts.append(f"[Document {i}: {file_name}]\n{chunk_text}")

    context_str = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are a helpful AI assistant for Highwatch AI. Answer the user's question based ONLY on the provided context documents below.

Rules:
- If the answer is clearly found in the documents, answer it concisely and accurately.
- If the answer is NOT in the documents, say exactly: "I don't have enough information in the provided documents to answer this."
- Always be professional and clear.
- Do not make up information.

Context Documents:
---
{context_str}
---

User Question: {query}

Answer:"""
    return prompt


def _call_groq(prompt: str) -> str:
    """Call Groq API with llama-3.3-70b-versatile model."""
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


def _call_gemini(prompt: str) -> str:
    """Call Google Gemini API."""
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()


def generate_answer(query: str, context_chunks: list[dict]) -> dict:
    """
    Generate a grounded answer using the LLM based on retrieved context.

    Args:
        query: User's natural language question.
        context_chunks: Top-k chunk dicts from FAISS search.

    Returns:
        dict with keys: answer (str), sources (list[str]), chunks_used (int)
    """
    if not context_chunks:
        return {
            "answer": "No documents have been indexed yet. Please run /sync-drive first.",
            "sources": [],
            "chunks_used": 0,
        }

    prompt = _build_prompt(query, context_chunks)

    try:
        if LLM_PROVIDER == "gemini":
            answer = _call_gemini(prompt)
        else:
            answer = _call_groq(prompt)
    except Exception as e:
        return {
            "answer": f"LLM error: {str(e)}",
            "sources": [],
            "chunks_used": len(context_chunks),
        }

    # Deduplicate sources while keeping doc_id
    sources_dict = {}
    for chunk in context_chunks:
        fname = chunk.get("file_name", "Unknown")
        if fname not in sources_dict:
            sources_dict[fname] = chunk.get("doc_id", "")
            
    sources = []
    for name, doc_id in sources_dict.items():
        if not doc_id or "/" in doc_id or "\\" in doc_id:
            # If doc_id is a local file path (from gdown), don't link to Drive
            link = "#"
        else:
            link = f"https://drive.google.com/file/d/{doc_id}/view"
        sources.append({"name": name, "link": link})

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(context_chunks),
    }


def generate_recommendations(sample_chunks: list[str]) -> list[str]:
    """Generate 3 suggested questions based on document content."""
    if not sample_chunks:
        return [
            "What is our refund policy?",
            "Summarize IT security SOP",
            "What are the compliance guidelines?"
        ]

    context_str = "\n\n".join(sample_chunks)
    prompt = f"""Based on the following snippets from a user's personal documents, suggest 3 natural language questions that the user might want to ask. 
Keep the questions short, diverse, and relevant to the content.
Return ONLY the questions, one per line, without numbers or bullets.

Document Snippets:
---
{context_str}
---

Suggested Questions:"""

    try:
        if LLM_PROVIDER == "gemini":
            raw_output = _call_gemini(prompt)
        else:
            raw_output = _call_groq(prompt)
        
        questions = [q.strip() for q in raw_output.split("\n") if q.strip()][:3]
        return questions
    except Exception:
        return [
            "What is our refund policy?",
            "Summarize IT security SOP",
            "What are the compliance guidelines?"
        ]
