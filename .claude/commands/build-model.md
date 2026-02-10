Build the SLM fine-tuning pipeline and inference server integration.

## 1. Training Data Preparation (`src/model/training_data.py`)

Generate 3 types of training data from processed documents:

**TYPE 1: Instruction-Following Pairs (SOP Assistant)** - Target 5000+ pairs
- Input: FIR summary + case category
- Output: Recommended investigation steps based on similar historical cases
- Generate using Claude API batch mode (use ANTHROPIC_API_KEY from .env)
- Example:
  Q: "FIR filed for theft at jewelry shop in Surat. CCTV available. No eyewitness."
  A: "1) Secure CCTV footage within 24hrs... 2) Door-to-door inquiry... 3) Check pawn shops..."

**TYPE 2: Chargesheet Quality Pairs** - Target 3000+ pairs
- Input: Draft chargesheet text
- Output: Quality assessment + missing elements
- Use historical data: chargesheets that led to conviction (good) vs acquittal (identify gaps)

**TYPE 3: Legal Q&A Pairs** - Target 5000+ pairs
- Generate from court rulings and bare acts
- Cover IPC/BNS sections, procedures, precedents
- Include Hindi and Gujarati pairs (not just English)

Format: JSONL with fields: instruction, input, output, language, category
Split: 90% train, 5% validation, 5% test
Save to: data/training/

Include quality filters to remove pairs with factual errors or low relevance.

## 2. QLoRA Fine-Tuning (`src/model/fine_tune.py`)

Fine-tune Mistral 7B using QLoRA:
- Base model: mistralai/Mistral-7B-Instruct-v0.3
- Quantization: 4-bit (BitsAndBytes)
- LoRA: r=64, alpha=16, dropout=0.1, targets=["q_proj","v_proj","k_proj","o_proj"]
- Training: lr=2e-4, batch=4, grad_accum=4, epochs=3
- Libraries: transformers, peft, bitsandbytes, trl (SFTTrainer)

Pipeline:
1. Load base model in 4-bit
2. Apply LoRA adapters
3. Train on instruction dataset
4. Evaluate on validation set after each epoch
5. Save best checkpoint
6. Merge LoRA weights with base
7. Export as GGUF for llama.cpp deployment

Wire up: `python -m src.cli model train`

## 3. Model Inference (`src/model/inference.py`)

Create inference client that talks to llama.cpp server:
- HTTP client for llama.cpp /completion endpoint
- Streaming support
- Temperature, top_p, top_k, repeat_penalty configuration
- Health check endpoint
- Fallback: if llama.cpp server not available, use transformers directly (slower)

Wire up: `python -m src.cli model evaluate` - run test prompts before/after fine-tuning

## 4. Evaluation (`src/model/evaluation.py`)

Evaluation dimensions:
- Retrieval: Recall@5, Precision@5, MRR on 100 test queries
- Generation: ROUGE-L, BERTScore vs reference answers
- Hallucination: check for non-existent IPC sections, wrong procedures
- Latency: end-to-end < 10 seconds target
- Multilingual: same query in en/hi/gu should give equivalent answers

Generate evaluation report as markdown.
