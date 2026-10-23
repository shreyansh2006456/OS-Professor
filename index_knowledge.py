
from pathlib import Path
import re

import chromadb
from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction,
)
from pypdf import PdfReader


PROJECT_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = PROJECT_DIR / "knowledge_base"
CHROMA_DIR = PROJECT_DIR / "chroma_db"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "os_knowledge"

SUPPORTED_FILES = {".pdf", ".txt", ".md"}


def read_file(path):
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    return path.read_text(encoding="utf-8", errors="ignore")


def chunk_text(text, chunk_size=1200, overlap=200):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def main():
    if not KNOWLEDGE_DIR.exists():
        print(
            f"Knowledge folder not found: {KNOWLEDGE_DIR}\n"
            "Create a folder named knowledge_base and put "
            "your OS PDFs, TXT, or Markdown notes inside it."
        )
        return

    embedding_function = SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )

    documents = []
    metadatas = []
    ids = []

    files = [
        path for path in KNOWLEDGE_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_FILES
    ]

    if not files:
        print("No PDF, TXT, or Markdown files were found.")
        return

    for path in files:
        print(f"Reading: {path.name}")

        try:
            text = read_file(path)
        except Exception as exc:
            print(f"Could not read {path.name}: {exc}")
            continue

        chunks = chunk_text(text)

        for index, chunk in enumerate(chunks):
            # Relative path avoids collisions between same-named files.
            relative_path = str(path.relative_to(KNOWLEDGE_DIR))
            chunk_id = f"{relative_path}::chunk::{index}"

            documents.append(chunk)
            ids.append(chunk_id)
            metadatas.append({
                "source": relative_path,
                "chunk": index,
            })

    if not documents:
        print("No readable text was found in the source documents.")
        return

    # Upsert makes re-indexing the same chunk IDs safe.
    # It does not automatically remove obsolete chunks.
    batch_size = 100

    for start in range(0, len(documents), batch_size):
        end = start + batch_size

        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )

        print(f"Indexed {min(end, len(documents))}/{len(documents)} chunks")

    print("Knowledge indexing complete.")
    print("Total chunks currently in collection:", collection.count())


if __name__ == "__main__":
    main()
