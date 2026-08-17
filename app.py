import os
import time
import uuid
import logging
import streamlit as st
from pathlib import Path

from config import (
    APP_TITLE, VERSION, LLM_MODEL, UPLOAD_DIR, MAX_FILE_MB, 
    MAX_PROMPT_CHARS, SOURCE_PREVIEW_CHARS
)
from utils import (
    sanitize_filename, safe_html, extract_article_numbers, build_pdf
)
from rag_engine import RAGEngine

# ── Optimisation UI ──────────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    """Cache le moteur pour éviter de recharger les embeddings à chaque clic."""
    eng = RAGEngine()
    eng.load_db()
    return eng

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="⚖️",
    layout="wide"
)

# Sidebar persistante
with st.sidebar:
    st.title(f"{APP_TITLE}")
    st.caption(f"v{VERSION} | Expert Juridique")
    
    app_mode = st.selectbox(
        "Menu Principal",
        ["💬 Assistant", "📁 Mes Documents", "📜 Historique"],
        key="navigation_select"
    )
    
    st.markdown("---")
    engine = get_engine()
    db_ok = engine.vector_db is not None
    st.status(f"Base de données : {'PRÊTE' if db_ok else 'VIDE'}", expanded=False)
    
    if st.button("🗑️ Purger la session"):
        st.session_state.messages = []
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIQUE DE CHAT (OPTIMISÉE)
# ═══════════════════════════════════════════════════════════════════════════════

if "messages" not in st.session_state:
    st.session_state.messages = []

if app_mode == "💬 Assistant":
    if not db_ok:
        st.info("👋 Bonjour ! Veuillez d'abord indexer vos documents dans l'onglet 'Mes Documents'.")
        st.stop()

    # Affichage rapide de l'historique
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "sources" in msg:
                with st.expander("📚 Sources consultées"):
                    for s in msg["sources"]:
                        st.caption(s[:500] + "...")

    # Traitement de la question
    if prompt := st.chat_input("Posez votre question juridique ici..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            try:
                # Analyse rapide de la question
                asked = extract_article_numbers(prompt, False)
                art_num = asked[0] if asked else None
                
                if art_num:
                    sys_prompt = f"Tu es un expert juridique marocain. Réponds précisément en français. Analyse l'Article {art_num}.\nCONTEXTE :\n{{context}}"
                else:
                    sys_prompt = "Tu es un expert juridique marocain. Réponds précisément en français.\nCONTEXTE :\n{context}"
                
                with st.spinner("Analyse juridique en cours..."):
                    stream = engine.query(prompt, sys_prompt, art_num)
                    for chunk in stream:
                        if "answer" in chunk:
                            full_response += chunk["answer"]
                            response_placeholder.markdown(full_response + "▌")
                
                response_placeholder.markdown(full_response)
                
                # Sauvegarde immédiate
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_response
                })
                
            except Exception as e:
                st.error(f"Désolé, une erreur est survenue : {str(e)}")

elif app_mode == "📁 Mes Documents":
    st.header("📚 Gestionnaire de Bibliothèque")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    col1, col2 = st.columns(2)
    with col1:
        uploaded = st.file_uploader("Ajouter un Code de Loi (PDF)", type="pdf")
        if uploaded and st.button("Confirmer l'ajout"):
            with open(os.path.join(UPLOAD_DIR, uploaded.name), "wb") as f:
                f.write(uploaded.getbuffer())
            st.success("Fichier ajouté.")
            st.rerun()

    with col2:
        st.subheader("Fichiers présents")
        for f in os.listdir(UPLOAD_DIR):
            if f.endswith(".pdf"):
                st.text(f"📄 {f}")

    if st.button("🚀 Lancer l'analyse et l'indexation", type="primary"):
        paths = [os.path.join(UPLOAD_DIR, f) for f in os.listdir(UPLOAD_DIR) if f.endswith(".pdf")]
        if not paths:
            st.error("Aucun document trouvé.")
        else:
            bar = st.progress(0)
            def update_bar(p, t): bar.progress(p, text=t)
            if engine.index_documents(paths, update_bar):
                st.success("Indexation terminée ! L'IA est prête.")
                time.sleep(1)
                st.rerun()

elif app_mode == "📜 Historique":
    st.header("📜 Historique des échanges")
    if not st.session_state.messages:
        st.write("Aucun historique pour le moment.")
    else:
        for i, m in enumerate(reversed(st.session_state.messages)):
            with st.expander(f"Question {len(st.session_state.messages)-i}: {m['content'][:60]}..."):
                st.write(m['content'])
