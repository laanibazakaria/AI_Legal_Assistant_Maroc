import os
import re
import logging
import pickle
import shutil
from pathlib import Path
from collections import OrderedDict
from typing import List, Optional, Dict
from functools import lru_cache

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.retrievers import BM25Retriever
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.retrievers import EnsembleRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
import chromadb

from config import (
    DB_DIR, COLLECTION_NAME, EMBED_MODEL, LLM_MODEL, LLM_CTX, LLM_THREADS,
    TEMPERATURE, CHROMA_K, BM25_K, MIN_ARTICLE_CHARS, CHUNKS_CACHE, ARTICLE_CACHE
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# TRAITEMENT DU TEXTE (SIMPLIFIÉ POUR LA RAPIDITÉ)
# ═══════════════════════════════════════════════════════════════════════════════

def preprocess_page(text: str) -> str:
    """Nettoyage ultra-rapide."""
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

def merge_pages(all_docs: List[Document]) -> List[Document]:
    merged = OrderedDict()
    for doc in all_docs:
        src = doc.metadata.get("source", "unknown")
        if src not in merged: merged[src] = ""
        merged[src] += "\n\n" + doc.page_content
    
    return [Document(page_content=v, metadata={"source": k}) for k, v in merged.items()]

def split_by_article(docs: List[Document]) -> List[Document]:
    """Découpe simplifiée."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
    return splitter.split_documents(docs)

# ═══════════════════════════════════════════════════════════════════════════════
# ENGINE CORE (OPTIMISÉ)
# ═══════════════════════════════════════════════════════════════════════════════

class RAGEngine:
    def __init__(self):
        self.embeddings = self._get_embeddings()
        self.vector_db = None
        self.bm25_retriever = None
        self.article_map = {}
        self.llm = None

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_embeddings():
        """Cache global pour éviter de recharger 500MB en RAM à chaque appel."""
        return HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": "cpu"}
        )

    def get_llm(self):
        if not self.llm:
            self.llm = OllamaLLM(
                model=LLM_MODEL,
                num_ctx=LLM_CTX,
                num_thread=LLM_THREADS,
                temperature=TEMPERATURE
            )
        return self.llm

    def load_db(self):
        if os.path.exists(DB_DIR) and os.listdir(DB_DIR):
            try:
                client = chromadb.PersistentClient(path=os.path.abspath(DB_DIR))
                self.vector_db = Chroma(client=client, embedding_function=self.embeddings, collection_name=COLLECTION_NAME)
                if os.path.exists(CHUNKS_CACHE):
                    with open(CHUNKS_CACHE, "rb") as f:
                        chunks = pickle.load(f)
                        self.bm25_retriever = BM25Retriever.from_documents(chunks, k=2)
                return True
            except Exception: pass
        return False

    def clear_db(self):
        """Vide la base de données proprement sans supprimer les fichiers verrouillés."""
        if os.path.exists(DB_DIR):
            try:
                client = chromadb.PersistentClient(path=os.path.abspath(DB_DIR))
                client.delete_collection(COLLECTION_NAME)
            except Exception:
                pass
        self.vector_db = None
        self.bm25_retriever = None

    def index_documents(self, pdf_paths: List[str], progress_callback=None):
        all_docs = []
        for i, path in enumerate(pdf_paths):
            if progress_callback: progress_callback((i+1)/len(pdf_paths), f"Lecture : {os.path.basename(path)}")
            loader = PyPDFLoader(path)
            all_docs.extend(loader.load())
        
        chunks = split_by_article(merge_pages(all_docs))
        
        client = chromadb.PersistentClient(path=DB_DIR)
        try: client.delete_collection(COLLECTION_NAME)
        except Exception: pass

        self.vector_db = Chroma.from_documents(chunks, self.embeddings, client=client, collection_name=COLLECTION_NAME)
        self.bm25_retriever = BM25Retriever.from_documents(chunks, k=2)
        
        with open(CHUNKS_CACHE, "wb") as f: pickle.dump(chunks, f)
        return True

    def query(self, prompt: str, system_prompt: str, art_num: Optional[str] = None):
        if not self.vector_db: raise ValueError("Base vide")
        
        v_ret = self.vector_db.as_retriever(search_kwargs={"k": 3})
        retriever = EnsembleRetriever(retrievers=[self.bm25_retriever, v_ret], weights=[0.3, 0.7]) if self.bm25_retriever else v_ret

        qa_prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])
        chain = create_retrieval_chain(retriever, create_stuff_documents_chain(self.get_llm(), qa_prompt))
        return chain.stream({"input": prompt})
