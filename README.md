# 🌸 Cozy AI Productivity & RAG Memory System

A cute, simplified, and interview-ready AI Productivity System featuring a **Cute & Cozy UI** (inspired by PixelBrew Studio's *Cozy Habit Tracker*), strict **2-Table Database Architecture**, **11 Productivity Analytics Metrics**, and a **Multi-Agent Retrieval-Augmented Generation (RAG) Task Memory Pipeline**.

---

## 🌟 Highlights

1. **Cute & Cozy Soft Pastel Aesthetic**: Soft pastel colors (`#FFDFE5`, `#FAF6F0`, `#EDE9FE`), pill-shaped badges, rounded `3xl`/`4xl` cards, and cute mascot doodles.
2. **Strict Minimalist Scope**: Focuses purely on Tasks, Analytics, and RAG Memory. No bloated modules.
3. **Strict 2-Table Schema**:
   - `Users` (`id`, `name`, `email`, `password_hash`, `created_at`)
   - `Tasks` (`id`, `user_id`, `title`, `description`, `priority`, `status`, `due_date`, `created_at`, `completed_at`, `estimated_minutes`, `actual_minutes`)
4. **Natural Language RAG Memory Engine**:
   - Translates task lifecycle events into natural-language memory strings stored in `ChromaDB` with `SentenceTransformers` embeddings.
   - Examples:
     - *"Completed React assignment in 45 minutes before the deadline."*
     - *"Postponed Database assignment three times."*
     - *"Finished DSA practice two days late."*
5. **Multi-Agent RAG Architecture**:
   - **Retrieval Agent**: Hybrid semantic search over user vector memories.
   - **Evaluator Agent**: Computes relevance confidence score & prevents hallucinations.
   - **Multi-LLM Query Agent**: Router supporting **Ollama** (local default), **OpenAI (ChatGPT)**, **Google Gemini**, and **xAI Grok**.

---

## 🚀 How to Set Up & Run

### Option 1: Quick Local Development (Recommended)

#### 1. Backend Setup (FastAPI + ChromaDB)
```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI dev server
uvicorn main:app --reload --port 8000
```
> The backend server will automatically seed default sample data and start running at `http://localhost:8000`. Interactive API Docs are available at `http://localhost:8000/docs`.

#### 2. Frontend Setup (React + Vite + Tailwind CSS)
```bash
# In a new terminal window, navigate to frontend
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```
> Open your browser at `http://localhost:3000`.

---

### Option 2: Docker Compose (One-Command Deployment)

Make sure Docker Desktop is installed and running, then execute:
```bash
docker-compose up --build
```
- **Frontend App**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`

---

## 🔑 Environment Variables (.env)

| Variable | Default Value | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./cozy_productivity.db` | SQLAlchemy Connection string (SQLite / PostgreSQL) |
| `JWT_SECRET_KEY` | `cozy_rag_productivity_tracker_super_secret_key_2026` | Secret key for JWT token generation |
| `OLLAMA_HOST` | `http://localhost:11434/api/generate` | Local Ollama endpoint |
| `OPENAI_API_KEY` | *(Optional)* | OpenAI API key for ChatGPT query provider |
| `GEMINI_API_KEY` | *(Optional)* | Google Gemini API key |
| `GROK_API_KEY` | *(Optional)* | xAI Grok API key |

---

## 📚 Architectural Deep-Dive: RAG & Vector Engine Notes

### 1. Neo4j Graph Database (GraphRAG Integration)
While ChromaDB handles vector embeddings, high-scale productivity engines map task dependencies to a Knowledge Graph:
```
(User)-[:COMPLETED]->(Task: React Assignment)-[:CATEGORY]->(Category: Frontend)
(User)-[:POSTPONED]->(Task: Database Exam)-[:BLOCKED_BY]->(Exam Period)
```
GraphRAG enables multi-hop reasoning like *"User consistently delays database assignments when exam period overlaps with frontend deadlines."*

### 2. FAISS / TurboVec Vector Search
For ultra-fast vector retrieval across millions of entries, **FAISS** (Facebook AI Similarity Search) or **TurboVec** can be plugged into the `RetrievalAgent` to achieve sub-millisecond similarity scoring.

### 3. Multi-Agent Pipeline Execution Flow
```
User Query -> [1. Retrieval Agent] -> Fetches Top-K Memories from ChromaDB
            -> [2. Evaluator Agent] -> Scores Relevancy & Filters Noisy Memory Context
            -> [3. Multi-LLM Agent] -> Generates Grounded Answer via Ollama/OpenAI/Gemini/Grok
```
