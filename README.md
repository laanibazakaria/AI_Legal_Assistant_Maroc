# ⚖️ AI Legal Assistant - Maroc

Assistant juridique intelligent basé sur le RAG (Retrieval-Augmented Generation) pour le droit marocain.

## 🚀 Fonctionnalités
- 💬 **Chat Juridique :** Posez des questions sur vos documents PDF.
- 📚 **Support Multilingue :** Analyse et réponse en Français et en Arabe (RTL).
- 📑 **Découpage par Article :** L'IA comprend la structure des lois marocaines.
- 📄 **Rapports PDF :** Générez des rapports de consultation exportables.
- 🔍 **Ensemble Retrieval :** Combine la recherche vectorielle (ChromaDB) et textuelle (BM25).
- 📷 **OCR Intégré :** Support des documents scannés via Tesseract.

## 🛠️ Architecture
- `app.py` : Interface utilisateur Streamlit.
- `rag_engine.py` : Moteur de recherche et de génération.
- `utils.py` : Fonctions utilitaires (PDF, Nettoyage, Langue).
- `config.py` : Configuration centralisée.

## 📦 Installation
1. Installez [Ollama](https://ollama.com/) et téléchargez le modèle :
   ```bash
   ollama run gemma2:2b
   ```
2. Installez les dépendances Python :
   ```bash
   pip install -r requirements.txt
   ```
3. Installez Tesseract OCR sur votre système pour le support des PDF scannés.

## 🏁 Lancement
```bash
streamlit run app.py
```

## ⚖️ Avertissement
Cet assistant est un outil d'aide à la recherche et ne remplace en aucun cas les conseils d'un professionnel du droit.
