"""Logika RAG: indexing, retrieval, dan generasi jawaban. Tidak ada kode UI di sini."""

import os
import tempfile

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from prompts import ANSWER_PROMPT


class PDFLimitError(Exception):
    """PDF melebihi batas yang diizinkan."""


def build_vectorstore(
    file_bytes, api_key, embed_model, chunk_size, chunk_overlap, max_pages=None
):
    """PDF -> potongan teks -> embedding -> FAISS. Mengembalikan (store, n_halaman, n_potongan)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        path = tmp.name
    try:
        pages = PyPDFLoader(path).load() 
    finally:
        os.remove(path)

    if max_pages and len(pages) > max_pages:
        raise PDFLimitError(
            f"PDF terlalu panjang: {len(pages)} halaman. Batasnya {max_pages} halaman."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(pages)
    embeddings = GoogleGenerativeAIEmbeddings(model=embed_model, google_api_key=api_key)
    return FAISS.from_documents(chunks, embeddings), len(pages), len(chunks)


def retrieve(vectorstore, question, k):
    """Ambil k potongan paling mirip, diberi nomor sumber mulai dari 1."""
    docs = vectorstore.similarity_search(question, k=k)
    return [
        {"id": i, "page": d.metadata.get("page", 0) + 1, "text": d.page_content}
        for i, d in enumerate(docs, start=1)
    ]


def _to_text(content):
    """Model Gemini baru bisa mengembalikan list blok konten, bukan string biasa."""
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)


def generate_answer(question, sources, api_key, chat_model):
    """Kirim pertanyaan + sumber bernomor ke LLM, kembalikan teks jawaban."""
    context = "\n\n".join(
        f"[{s['id']}] (Halaman {s['page']})\n{s['text']}" for s in sources
    )
    llm = ChatGoogleGenerativeAI(
        model=chat_model, temperature=0.2, google_api_key=api_key
    )
    prompt = ANSWER_PROMPT.format(context=context, question=question)
    return _to_text(llm.invoke(prompt).content)