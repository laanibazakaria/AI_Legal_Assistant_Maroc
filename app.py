import streamlit as st
import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Configuration de la page
st.set_page_config(page_title="AI Legal Assistant - Maroc", page_icon="⚖️", layout="wide")

st.title("⚖️ AI Legal Assistant - Maroc")
st.markdown("---")

# Dossier pour la base de données vectorielle
DB_DIR = "chroma_db_web"

# Initialisation du modèle d'embeddings (mis en cache pour la performance)
@st.cache_resource
def load_embeddings():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

embeddings = load_embeddings()

# Barre latérale pour l'upload
with st.sidebar:
    st.header("📁 Documents")
    uploaded_files = st.file_uploader("Chargez vos documents juridiques (PDF)", type="pdf", accept_multiple_files=True)
    
    if uploaded_files:
        if st.button(f"🚀 Analyser les {len(uploaded_files)} documents"):
            with st.spinner("Analyse et indexation en cours..."):
                all_docs = []
                for uploaded_file in uploaded_files:
                    # Sauvegarde temporaire de chaque fichier
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name

                    # 1. Loading
                    loader = PyPDFLoader(tmp_path)
                    all_docs.extend(loader.load())
                    os.remove(tmp_path)

                # 2. Chunking
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                chunks = text_splitter.split_documents(all_docs)

                # 3. Vector DB (On recrée la base avec tous les documents)
                st.session_state.vector_db = Chroma.from_documents(
                    documents=chunks,
                    embedding=embeddings,
                    persist_directory=DB_DIR
                )
                st.success(f"{len(uploaded_files)} documents analysés et indexés !")

# Zone de Chat
st.header("💬 Chat avec l'Expert Juridique")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 Sources consultées"):
                for src in message["sources"]:
                    st.info(src)

# Input de l'utilisateur
if prompt := st.chat_input("Posez votre question sur le droit marocain..."):
    if "vector_db" not in st.session_state:
        st.error("Veuillez d'abord charger un document dans la barre latérale.")
    else:
        # Afficher le message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Réponse de l'IA
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            source_docs = []
            
            with st.spinner("Recherche dans les documents..."):
                try:
                    llm = Ollama(model="qwen2:1.5b")
                    
                    system_prompt = (
                        "Tu es un assistant juridique expert au Maroc. "
                        "IMPORTANT: Tu dois détecter la langue de la question (Arabe, Français ou Anglais) "
                        "et répondre obligatoirement dans cette MÊME LANGUE. "
                        "Si la question est en ARABE, réponds en ARABE. "
                        "Si la question est en FRANÇAIS, réponds en FRANÇAIS. "
                        "Utilise les extraits fournis pour ta réponse.\n\n"
                        "CONTEXTE JURIDIQUE :\n{context}"
                    )
                    
                    qa_prompt = ChatPromptTemplate.from_messages([
                        ("system", system_prompt),
                        ("human", "{input}"),
                    ])

                    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
                    rag_chain = create_retrieval_chain(st.session_state.vector_db.as_retriever(), question_answer_chain)

                    # Streaming de la réponse
                    for chunk in rag_chain.stream({"input": prompt}):
                        if "context" in chunk:
                            source_docs = chunk["context"]
                        if "answer" in chunk:
                            full_response += chunk["answer"]
                            placeholder.markdown(full_response + "▌")
                    
                    placeholder.markdown(full_response)
                    
                    # Affichage des sources
                    sources_content = []
                    if source_docs:
                        with st.expander("📚 Sources consultées"):
                            for i, doc in enumerate(source_docs):
                                st.markdown(f"**Extrait {i+1} :**")
                                st.info(doc.page_content)
                                sources_content.append(doc.page_content)
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": full_response,
                        "sources": sources_content
                    })
                    
                except Exception as e:
                    st.error(f"Erreur : {e}")
