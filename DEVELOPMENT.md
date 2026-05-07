# Local Development & Testing Guide

## 🚀 Quick Start - Simple 2-Terminal Setup

### Prerequisites: Setup (One Time Only)

**If you haven't set up yet, run this once:**

```bash
# Clone repo
git clone <your-repo-url>
cd production-rag-system

# Create & activate venv
python -m venv venv
venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate  # Mac/Linux

# Install backend deps
pip install -r backend/requirements.txt

# Install frontend deps
cd frontend/react-app
npm install
cd ../..
```

### Step 2: Run Backend & Frontend

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
# Server ready at http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend/react-app
npm run dev
# App ready at http://localhost:3000
```

## ⚡ Run Backend & Frontend (Every Time)

Open 2 terminal windows and run these commands:

**Terminal 1 - Backend (stays running):**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```
You should see: `Application startup complete` ✓

**Terminal 2 - Frontend (stays running):**
```bash
cd frontend/react-app
npm run dev
```
You should see: `VITE v... ready in ... ms` ✓

Then open `http://localhost:3000` in your browser.

---

## ✅ How to Test Everything Works

### Test 1: Frontend Loads Correctly
- Open http://localhost:3000
- You should see the RAG System UI with:
  - Hero section with title "Production RAG System"
  - Stats showing document count and paragraph count
  - Query input form

### Test 2: Query Works End-to-End
1. In the UI, type a question (e.g., "What is the system about?")
2. Click "Run retrieval"
3. Wait 1-2 seconds
4. You should see the AI response + source documents below

### Test 3: Backend API Directly (Optional)
```bash
# In another terminal, test backend directly:
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the system?"}'

# Expected response: {"answer": "...", "sources": [...]}
```

---

## 🧪 Test Scenarios (Optional)

### Scenario 1: Basic Query
```
Input: "How does the backend work?"
Expected: Answer about FastAPI service + retrieved sources
Button: "Run retrieval"
Result: ✅ Should show answer + 1-2 source cards
```

### Scenario 2: Re-index Documents
```
1. Add a new .md file to data/documents/
   Example: data/documents/my-doc.md
   Content: "# My Document\n\nSome content here..."

2. Click "Re-index documents" button
3. Wait 1-2 seconds
4. Check stats update
Result: ✅ Document count should increase
```

### Scenario 3: With Ollama (Optional)
```
1. Install Ollama from ollama.ai
2. In another terminal: ollama run llama2
   (First time: ~4GB download, takes 5-10 min)
3. Wait for "waiting for prompt"
4. Go back to app, click "Run retrieval"
Result: ✅ Backend logs should show Ollama response
         (If Ollama fails: fallback to mock is fine)
```

### Scenario 4: Multiple Queries
```
Try different question types:
- "How does RAG work?" → "how" template
- "Why use vector search?" → "why" template
- "What's the architecture?" → "architecture" template
- "Tell me about documents" → default template
Result: ✅ Each should trigger different templates
```

---

## 📊 Expected Behavior

| Component | Status | Expected |
|-----------|--------|----------|
| Backend API | ✅ | Starts without errors, logs "Application startup complete" |
| Frontend | ✅ | Builds & hot-reloads, page shows content |
| Sample doc | ✅ | "sample.md" loaded, stats show 1 document |
| Query | ✅ | Submit question → gets answer + sources |
| Re-index | ✅ | Click button → new docs indexed in background |
| Ollama | ⚠️ Optional | If running: uses real LLM; if not: mock response |

---

## 🐛 Debugging

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep fastapi

# Reinstall
pip install -r backend/requirements.txt --force-reinstall
```

### Frontend won't start
```bash
# Check Node version
node --version  # Should be 18+
npm --version

# Clean & reinstall
cd frontend/react-app
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Port 8000/3000 already in use
```bash
# Find what's using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Mac/Linux

# Kill process or use different port
python -m uvicorn main:app --port 8001 --reload
```

### Ollama connection error
```
Error: "Failed to connect to localhost:11434"
→ This is OK! Backend auto-fallbacks to mock response
→ If you want real LLM: run `ollama run llama2` in another terminal
```

---

## 📝 Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads at localhost:3000
- [ ] Document stats show (1 documents, 4 paragraphs)
- [ ] Can submit a query and get answer
- [ ] Answer includes source snippets
- [ ] Re-index button works
- [ ] Can add new .md file and re-index
- [ ] (Optional) Ollama integration works or fallback is smooth

---

## 🚀 Next Steps

After local testing works:
1. **Add more documents** to `data/documents/` (PDF → text, or write .md)
2. **Experiment with queries** (different keywords, phrasing)
3. **Try Ollama** for better responses
4. **Deploy to Railway/Vercel** (when ready for online testing)

