# WarrantyPatternMiner Setup Guide

This guide walks through setting up and running WarrantyPatternMiner on Windows, macOS, or Linux.

---

## 1. System Requirements
- **Python**: 3.11 or higher (Python 3.13 recommended)
- **Node.js**: 18.x or higher (Node 20+ / 22+ recommended)
- **npm**: 9.x or higher

---

## 2. Installation Steps

### Step 1: Clone Repository
```bash
git clone <repo-url>
cd WarrantyMiner
```

### Step 2: Python Backend Environment
```bash
# Optional: Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install Python requirements
pip install -r requirements.txt
```

### Step 3: Seed Database with Canonical Claims Dataset
```bash
python scripts/seed_database.py
```
This generates `canonical_warranty_claims.csv` (567 claims with the 17-claim canonical hidden defect) and seeds the SQLite database (`warranty_miner.db`).

### Step 4: Frontend Installation
```bash
cd apps/web
npm install
cd ../..
```

---

## 3. Running the Application

### Start Backend API:
```bash
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Start Frontend Console:
```bash
cd apps/web
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 4. Optional AI Configuration

By default, WarrantyPatternMiner uses a built-in deterministic hybrid NLP engine that runs locally with zero external API dependencies.

If you wish to enable Cloud LLMs or local Ollama:

### Option A: Local Ollama
1. Pull model: `ollama run llama3.2`
2. In `.env`:
   ```env
   USE_OLLAMA=true
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2
   ```

### Option B: Cloud Gemini / OpenAI
In `.env`:
```env
GEMINI_API_KEY=your_gemini_key_here
LLM_MODEL=gemini-2.5-flash
```
