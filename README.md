# 🧠 Highwatch AI — RAG System over Google Drive

> **"Your personal ChatGPT over Google Drive"**  
> A production-ready Retrieval-Augmented Generation (RAG) API with a beautiful frontend UI. It connects to your Google Drive, processes documents, and answers questions based *only* on your files.

---

## 🚀 Quick Start Guide

Follow these steps exactly to run the project on your local machine.

### 1. Prerequisites
- **Python 3.10+** installed on your system.
- A **Google Cloud Console** account (to get OAuth keys).
- A **Groq API Key** (for fast, free LLM inference).

### 2. Get Your API Keys

**Groq API Key:**
1. Go to [console.groq.com](https://console.groq.com) and sign up.
2. Click on "API Keys" and generate a new key.
3. Save this key, you will need it in the next step.

**Google OAuth Credentials:**
1. Go to [Google Cloud Console](https://console.cloud.google.com).
2. Create a project and search for **"Google Drive API"** → Click Enable.
3. Go to **APIs & Services → OAuth Consent Screen**. Select "External", fill in the basic details (app name, your email), and click Save.
4. On the OAuth Consent Screen page, scroll down to **Test Users**, click **"+ Add Users"** and add your own Google Drive email address. *(Crucial step!)*
5. Go to **APIs & Services → Credentials**.
6. Click **"+ Create Credentials"** → Choose **"OAuth 2.0 Client ID"**.
7. Application Type: **Web Application**.
8. Under **Authorized JavaScript origins**, add: `http://localhost:8000`
9. Under **Authorized redirect URIs**, add: `http://localhost:8000/auth/callback`
10. Click Create. Copy your `Client ID` and `Client Secret`.

### 3. Setup the Project

1. Clone or extract this repository to your computer.
2. Open your terminal and navigate into the folder:
   ```bash
   cd highminds
   ```
3. Create a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate    # Mac/Linux
   # venv\Scripts\activate     # Windows
   ```
4. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Rename `.env.example` to `.env` and fill in your keys:
   ```env
   GOOGLE_CLIENT_ID=your_client_id_from_step_2
   GOOGLE_CLIENT_SECRET=your_client_secret_from_step_2
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
   GROQ_API_KEY=your_groq_api_key_from_step_2
   LLM_PROVIDER=groq
   PORT=8000
   STORAGE_DIR=./storage
   DOWNLOAD_DIR=./downloads
   ```

### 4. Run the Application

Run the FastAPI server using uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Your app is now live! Open your browser and go to:
👉 **http://localhost:8000**

---

## 📂 Testing with Demo Documents

To test the system without connecting your personal Drive, you can use our pre-configured public demo folder!

**Anonymous Sync (Fastest Method):**
1. Start the app and go to `http://localhost:8000`.
2. Under "2. Sync Documents", paste the following link:
   `https://drive.google.com/drive/folders/1ZP8lXDro7XL3Kfyg2avmDwlSOcAgabc-?usp=sharing`
3. Click **"Sync Now"**. The app will securely download the 5 demo files and build your RAG index without requiring any Google login!

**OAuth Sync (Testing personal docs):**
1. Click **"Connect Drive"** and authenticate.
2. Upload your own PDFs or TXTs to your Drive.
3. Leave the folder link box empty and click **"Sync Now"**.

---

## ❓ Example Queries

Once the sync is complete, test the AI's capabilities using the chat box. The AI provides clickable source links that take you straight to the Google Drive file!

### Basic Retrieval (Easy)
Tests if the system can find a specific fact in a specific document.
- *"How many days do I have to submit a refund request?"*
- *"What is the minimum password length required by the IT security policy?"*
- *"How many days of paid sick leave do employees get?"*

### Synthesis & Multi-Step (Medium)
Tests if the system can grab chunks from different parts of a document and combine them logically.
- *"What is the step-by-step process for submitting an expense claim?"*
- *"Can I get a refund for a custom enterprise solution, and what about an annual subscription?"*
- *"What are the rules for domestic vs. international travel expenses?"*

### Hallucination Prevention (Hard / Edge Cases)
A good RAG system must refuse to answer questions if the information is not in the documents. 
- *"What is the company policy on bringing pets to the office?"*
- *"How much is the CEO's salary?"*
- *"Does the company provide free lunch on Fridays?"*

*(The AI should explicitly reply with: "I don't have enough information in the provided documents to answer this.")*

---

## 🏗️ Architecture & Features

- **Frontend:** HTML/CSS/JS (Vanilla) with real-time stats and clickable source links.
- **Backend API:** FastAPI (Python)
- **Drive Integration:** Google OAuth 2.0 + Drive API (with Incremental Sync support).
- **Text Processing:** PyPDF for PDFs, LangChain's RecursiveCharacterTextSplitter for overlapping chunks.
- **Embeddings:** `all-MiniLM-L6-v2` via SentenceTransformers (runs locally, free & fast).
- **Vector DB:** FAISS (`faiss-cpu`) for incredibly fast local similarity search.
- **LLM Engine:** Groq API running `llama-3.3-70b-versatile` for blazing fast generation.

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `Access blocked: App has not completed verification` | Go to Google Cloud Console → OAuth consent screen → Add your exact email to "Test users". |
| `Scope has changed from X to Y` | Handled automatically! We use `OAUTHLIB_RELAX_TOKEN_SCOPE=1`. |
| `Model decommissioned` | Handled! We are using the newest `llama-3.3-70b-versatile` model. |
| `ModuleNotFoundError` | Ensure you activated your virtual environment before running `uvicorn main:app`. |
