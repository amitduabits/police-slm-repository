Execute Phase 2 (RAG System + SLM Fine-Tuning) of the Gujarat Police SLM project.

Weeks 5-12. Two parallel tracks: RAG retrieval and SLM fine-tuning.

## Track A: RAG Pipeline

### Step 1: Build and test hybrid search
- Ensure embedding pipeline from Phase 1 is working
- Implement hybrid search (vector + keyword)
- Test with 10 queries per use case:
  - SOP queries: "theft investigation procedure", "murder scene evidence collection"
  - Chargesheet queries: "Section 302 chargesheet missing elements"
  - General: "bail conditions for NDPS cases in Gujarat"
- Report: retrieval scores, compare hybrid vs vector-only

### Step 2: Build re-ranking
- Add cross-encoder re-ranking on top-20 results
- Compare before/after re-ranking quality

### Step 3: Build context assembly and prompt templates
- Test full RAG pipeline: query → retrieve → assemble → prompt → generate

## Track B: Fine-Tuning

### Step 4: Prepare training data
- Generate instruction-following pairs from collected data
- Use Claude API batch mode for synthetic data generation
- Target: 13000+ training pairs (5000 instruction, 3000 chargesheet, 5000 QA)
- Save to data/training/

### Step 5: Fine-tune with QLoRA
- Load Mistral 7B base in 4-bit
- Train for 3 epochs on T4 GPU (~8-12 hours)
- Save checkpoints, track loss curves

### Step 6: Export and deploy
- Merge LoRA weights
- Export to GGUF format
- Deploy via llama.cpp server

## Evaluation

### Step 7: Run full evaluation
- Retrieval: Recall@5, Precision@5 on 100 test queries → target ≥80%
- Generation: expert-style rating on 50 test cases → target ≥3.5/5
- Hallucination: check for false section numbers → target <5%
- Latency: end-to-end → target <10 seconds
- Multilingual: test 30 queries in en/hi/gu

### Step 8: Phase 2 Report
Generate data/phase2_report.md with:
- Side-by-side: base Mistral vs fine-tuned on 10 police-domain questions
- RAG retrieval quality metrics
- End-to-end test results
- Performance benchmarks (latency, memory, GPU usage)

Print "PHASE 2 COMPLETE" when done.
