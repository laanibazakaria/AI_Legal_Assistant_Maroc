import os
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# TITRES & IDENTITÉ
# ═══════════════════════════════════════════════════════════════════════════════
APP_TITLE = "⚖️ Assistant Juridique Maroc"
VERSION = "1.1.0"

# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLES & IA (Optimisés pour la rapidité)
# ═══════════════════════════════════════════════════════════════════════════════
LLM_MODEL = "gemma2:2b"
# Utilisation d'un modèle plus rapide et léger pour les embeddings
EMBED_MODEL = "all-MiniLM-L6-v2" 
LLM_CTX = 2048 # Réduit pour gagner en vitesse de réponse
LLM_THREADS = 6 # Augmenté pour paralléliser davantage si possible
TEMPERATURE = 0.0 # Plus déterministe et rapide pour le juridique

# ═══════════════════════════════════════════════════════════════════════════════
# CHEMINS & RÉPERTOIRES
# ═══════════════════════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent.resolve()
DB_DIR = str(BASE_DIR / "chroma_db")
UPLOAD_DIR = str(BASE_DIR / "uploads")
DOCS_DIR = str(BASE_DIR / "documents")  # Dossier par défaut pour les docs système

# ═══════════════════════════════════════════════════════════════════════════════
# CACHE & PERSISTENCE
# ═══════════════════════════════════════════════════════════════════════════════
CACHE_VERSION = "v7"
CHUNKS_CACHE = f"chunks_{CACHE_VERSION}.pkl"
ARTICLE_CACHE = f"articles_{CACHE_VERSION}.pkl"
COLLECTION_NAME = "legal_docs"

# ═══════════════════════════════════════════════════════════════════════════════
# PARAMÈTRES RAG
# ═══════════════════════════════════════════════════════════════════════════════
MAX_FILE_MB = 50
MAX_PROMPT_CHARS = 2000
BM25_K = 5
CHROMA_K = 5
MIN_ARTICLE_CHARS = 30
SOURCE_PREVIEW_CHARS = 4000
CHUNK_SIZE = 3000
CHUNK_OVERLAP = 300

# ═══════════════════════════════════════════════════════════════════════════════
# RESSOURCES & POLICES
# ═══════════════════════════════════════════════════════════════════════════════
# Chemin relatif vers la police DejaVu pour le support Arabe dans les PDF
DEJAVU_FONT = str(BASE_DIR / "DejaVuSans.ttf")
DEJAVU_BOLD = str(BASE_DIR / "DejaVuSans-Bold.ttf")
DEJAVU_OBLIQUE = str(BASE_DIR / "DejaVuSans-Oblique.ttf")
