import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama

# Nouvelles méthodes pour les versions récentes de LangChain
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# 1. Configuration des chemins
DOCS_DIR = r"C:\Users\laani\Desktop\AI_Legal_Assistant_Maroc\documents"
DB_DIR = r"C:\Users\laani\Desktop\AI_Legal_Assistant_Maroc\chroma_db"

def run_rag():
    print("🚀 Chargement des documents...")
    all_documents = []
    if not os.path.exists(DOCS_DIR):
        print(f"❌ Erreur : Le dossier {DOCS_DIR} n'existe pas.")
        return

    for file in os.listdir(DOCS_DIR):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(DOCS_DIR, file))
            all_documents.extend(loader.load())

    if not all_documents:
        print("⚠️ Aucun document PDF trouvé dans le dossier documents.")
        return

    # 2. Chunking (Découpage)
    print("✂️ Découpage des textes en morceaux...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(all_documents)

    # 3. Embeddings
    print("🧠 Création des Embeddings (HuggingFace)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 4. Vector Database
    print("📁 Création/Chargement de la base de données vectorielle...")
    vector_db = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings,
        persist_directory=DB_DIR
    )

    # 5. Setup LLM & Prompt
    print("🤖 Initialisation de l'IA (Ollama - TinyLlama)...")
    try:
        llm = Ollama(model="tinyllama")
        
        # Création du template de prompt professionnel
        system_prompt = (
            "Tu es un assistant juridique expert au Maroc. "
            "Utilise les extraits de documents fournis ci-dessous pour répondre à la question. "
            "Si tu ne connais pas la réponse, dis simplement que tu ne sais pas. "
            "Sois précis et professionnel."
            "\n\n"
            "{context}"
        )
        
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

        # Création de la chaine de récupération
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(vector_db.as_retriever(), question_answer_chain)

        # 6. Test de la question
        query = "Quels sont les éléments qui composent le fonds de commerce d'après le texte ?"
        print(f"\n❓ Question : {query}")
        
        response = rag_chain.invoke({"input": query})
        
        print("\n✅ Réponse de l'IA :")
        print("-" * 50)
        print(response["answer"])
        print("-" * 50)
        
    except Exception as e:
        print(f"\n❌ Erreur : {e}")

if __name__ == "__main__":
    run_rag()
