from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(
    text: str,
    file_name: str,
    file_id: str,
    source: str = "gdrive",
) -> list[dict]:
    """
    Split extracted text into overlapping chunks with attached metadata.

    Args:
        text: Full extracted text from a document.
        file_name: Original Drive file name (used as source citation).
        file_id: Google Drive file ID (used as doc identifier).
        source: Source tag — default "gdrive".

    Returns:
        List of chunk dicts: { chunk_text, doc_id, file_name, source, chunk_index }
    """
    if not text or not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    raw_chunks = splitter.split_text(text)

    chunks = []
    for i, chunk in enumerate(raw_chunks):
        chunk = chunk.strip()
        if len(chunk) < 20:  # skip tiny meaningless chunks
            continue
        chunks.append(
            {
                "chunk_text": chunk,
                "doc_id": file_id,
                "file_name": file_name,
                "source": source,
                "chunk_index": i,
            }
        )

    return chunks
