Execute Sprint 2: Get RAG pipeline working end-to-end.

PREREQUISITE: Sprint 1 must be complete (docs embedded in ChromaDB, search returning results).

Goal: Type a question → get an AI-generated answer with source citations.

## TASK 1: Set up Mistral 7B inference (30 min)

We need a running LLM to generate answers. Two options depending on hardware:

**Option A: llama.cpp (if you have GPU or decent CPU)**
```bash
# Download quantized model (~4GB)
# Use TheBloke's GGUF quantization
pip install huggingface_hub
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download(repo_id='TheBloke/Mistral-7B-Instruct-v0.2-GGUF',
                filename='mistral-7b-instruct-v0.2.Q4_K_M.gguf',
                local_dir='models/')
"

# Install and run llama-cpp-python (includes server)
pip install llama-cpp-python[server]

# Start server
python -m llama_cpp.server --model models/mistral-7b-instruct-v0.2.Q4_K_M.gguf --host 0.0.0.0 --port 8080 --n_ctx 4096
```

**Option B: Use Ollama (easier on Windows)**
```bash
# If Ollama is installed:
ollama pull mistral
# Server runs automatically on port 11434
```

**Option C: Use Claude API as temporary LLM (fastest to get working)**
If model download is slow, temporarily use Claude API for development:
```python
# In .env, set ANTHROPIC_API_KEY
# Create a thin wrapper that calls Claude API
# IMPORTANT: This is ONLY for development. Production must be on-premise.
```

Create `src/model/inference.py`:
```python
class LLMClient:
    """Unified LLM client - supports llama.cpp, Ollama, or Claude API."""
    
    def __init__(self, backend="llamacpp", base_url="http://localhost:8080"):
        self.backend = backend
        self.base_url = base_url
    
    def generate(self, prompt: str, max_tokens=2048, temperature=0.1) -> str:
        """Generate text from prompt."""
        if self.backend == "llamacpp":
            return self._llamacpp_generate(prompt, max_tokens, temperature)
        elif self.backend == "ollama":
            return self._ollama_generate(prompt, max_tokens, temperature)
        elif self.backend == "claude":
            return self._claude_generate(prompt, max_tokens, temperature)
    
    def _llamacpp_generate(self, prompt, max_tokens, temperature):
        response = requests.post(f"{self.base_url}/completion", json={
            "prompt": prompt, "n_predict": max_tokens, "temperature": temperature
        })
        return response.json()["content"]
    
    def _ollama_generate(self, prompt, max_tokens, temperature):
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "mistral", "prompt": prompt, "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens}
        })
        return response.json()["response"]
    
    def _claude_generate(self, prompt, max_tokens, temperature):
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=max_tokens,
              messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text
    
    def health_check(self) -> bool:
        """Check if LLM server is running."""
        try:
            if self.backend == "llamacpp":
                r = requests.get(f"{self.base_url}/health")
                return r.status_code == 200
            elif self.backend == "ollama":
                r = requests.get("http://localhost:11434/api/tags")
                return r.status_code == 200
            elif self.backend == "claude":
                return bool(os.environ.get("ANTHROPIC_API_KEY"))
        except:
            return False
```

## TASK 2: Wire up RAG Pipeline (30 min)

Update `src/retrieval/rag_pipeline.py` to connect everything:
1. Load the embedding model and ChromaDB client from Sprint 1
2. Connect to the LLM client from Task 1
3. Make `query()` method work end-to-end:
   - Take user question
   - Expand query with legal terms
   - Search ChromaDB for relevant chunks
   - Assemble context with source citations
   - Send to LLM with prompt template
   - Return answer + citations

## TASK 3: Create prompt templates (20 min)

Create `src/retrieval/prompts.py` with tested prompt templates:

**SOP Assistant prompt:**
```
You are an AI assistant for Gujarat Police officers. Based on the following case documents from similar past cases, suggest investigation steps.

REFERENCE CASES:
{context}

CURRENT FIR DETAILS:
{query}

Provide your response as:
1. CRITICAL STEPS (must do within 24 hours):
2. IMPORTANT STEPS (within 1 week):
3. RECOMMENDED STEPS:

For each step, cite which reference case informed this recommendation.
Always mention relevant IPC/BNS sections.
Respond in English. Be specific and actionable.
```

**Chargesheet Review prompt:**
```
You are an AI legal assistant reviewing a chargesheet for Gujarat Police. Compare the draft against successful chargesheets from similar cases.

REFERENCE SUCCESSFUL CHARGESHEETS:
{context}

DRAFT CHARGESHEET TO REVIEW:
{query}

Provide:
1. COMPLETENESS SCORE: X/100
2. MISSING ELEMENTS (critical gaps):
3. WEAK POINTS (areas needing strengthening):
4. STRENGTHS (well-done elements):
5. RECOMMENDATIONS:

Cite specific sections and reference cases. Be precise about what's missing.
```

**General Q&A prompt:**
```
You are a legal knowledge assistant for Gujarat Police. Answer the following question using ONLY the provided source documents. Always cite your sources.

SOURCE DOCUMENTS:
{context}

QUESTION: {query}

ANSWER (cite sources for every claim):
```

## TASK 4: Test End-to-End (15 min)

Create `scripts/test_rag.py`:
```python
"""Quick test script to verify RAG pipeline works end-to-end."""
from src.retrieval.rag_pipeline import RAGPipeline
from src.retrieval.embeddings import EmbeddingPipeline
from src.model.inference import LLMClient

# Initialize
embedder = EmbeddingPipeline()
llm = LLMClient(backend="ollama")  # or "llamacpp" or "claude"

rag = RAGPipeline(
    chroma_client=embedder.client,
    embedding_model=embedder.model,
    llm_client=llm,
)

# Test queries
test_queries = [
    ("What is the punishment for murder under IPC Section 302?", "general"),
    ("FIR filed for theft at jewelry shop in Surat. CCTV available. Suggest investigation steps.", "sop"),
    ("What are the bail conditions for NDPS Act cases?", "general"),
]

for query, use_case in test_queries:
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"USE CASE: {use_case}")
    result = rag.query(query, use_case=use_case)
    print(f"RESPONSE: {result['response'][:500]}")
    print(f"CITATIONS: {result['citations']}")
    print(f"NUM RESULTS: {result['num_results']}")
```

Run: `python scripts/test_rag.py`

## DONE CRITERIA:
- LLM server running (any backend)
- RAG pipeline returns answers with citations for test queries
- Prompt templates produce high-quality, structured responses
- Print "SPRINT 2 COMPLETE - RAG WORKING"
