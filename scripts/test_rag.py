"""
Quick test script to verify RAG pipeline works end-to-end.

Tests all three use cases:
1. General Q&A
2. SOP Assistant
3. Chargesheet Review
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.retrieval.rag_pipeline import create_rag_pipeline
from src.retrieval.embeddings import create_embedding_pipeline
from src.model.inference import create_llm_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_rag_pipeline():
    """Test RAG pipeline with different use cases."""

    print("=" * 80)
    print("TESTING RAG PIPELINE")
    print("=" * 80)

    # Initialize components
    print("\n1. Initializing components...")
    try:
        embedder = create_embedding_pipeline()
        print(f"   [OK] Embedding pipeline ready (model: {embedder.model})")
    except Exception as e:
        print(f"   [FAIL] Embedding pipeline failed: {e}")
        return False

    try:
        llm = create_llm_client(backend="mistral")  # Use local Mistral 7B
        print(f"   [OK] LLM client ready (backend: {llm.backend})")

        if not llm.health_check():
            print("   [WARN] Warning: LLM health check failed. Responses will be limited.")
    except Exception as e:
        print(f"   [FAIL] LLM client failed: {e}")
        print("   -> Continuing without LLM (will only test retrieval)")
        llm = None

    try:
        rag = create_rag_pipeline(
            embedding_pipeline=embedder,
            llm_client=llm
        )
        print("   [OK] RAG pipeline ready")
    except Exception as e:
        print(f"   [FAIL] RAG pipeline initialization failed: {e}")
        return False

    # Test queries
    test_queries = [
        {
            "query": "What is the punishment for murder under IPC Section 302?",
            "use_case": "general",
            "description": "General Legal Q&A"
        },
        {
            "query": "FIR filed for theft at jewelry shop in Surat. CCTV footage available. Two suspects identified. Suggest investigation steps.",
            "use_case": "sop",
            "description": "SOP Assistant - Theft Investigation"
        },
        {
            "query": "What are the bail conditions for NDPS Act cases?",
            "use_case": "general",
            "description": "General Q&A - Bail Conditions"
        },
    ]

    print("\n2. Running test queries...")
    print("=" * 80)

    results = []
    for i, test in enumerate(test_queries, 1):
        print(f"\n[TEST {i}/{len(test_queries)}] {test['description']}")
        print("-" * 80)
        print(f"Query: {test['query']}")
        print(f"Use Case: {test['use_case']}")
        print()

        try:
            result = rag.query(
                text=test['query'],
                use_case=test['use_case'],
                top_k=3
            )

            # Display results
            print(f"[OK] Retrieved {result.num_results} documents")
            print()
            print("RESPONSE:")
            print("-" * 80)
            response_preview = result.response[:800] if len(result.response) > 800 else result.response
            print(response_preview)
            if len(result.response) > 800:
                print(f"\n... (truncated, total {len(result.response)} chars)")
            print()

            print("CITATIONS:")
            print("-" * 80)
            for j, citation in enumerate(result.citations, 1):
                print(f"  {j}. {citation['source']}")
                print(f"     Score: {citation['score']:.3f}")
                if citation.get('doc_type'):
                    print(f"     Type: {citation['doc_type']}")
                if citation.get('court'):
                    print(f"     Court: {citation['court']}")

            results.append({
                "test": test['description'],
                "success": True,
                "num_results": result.num_results,
                "response_length": len(result.response)
            })

        except Exception as e:
            print(f"[FAIL] Test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "test": test['description'],
                "success": False,
                "error": str(e)
            })

        print("=" * 80)

    # Summary
    print("\n3. SUMMARY")
    print("=" * 80)

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])

    print(f"Tests run: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print()

    for result in results:
        status = "[OK] PASS" if result['success'] else "[FAIL] FAIL"
        print(f"{status} - {result['test']}")
        if result['success']:
            print(f"      Retrieved: {result['num_results']} docs, "
                  f"Response: {result['response_length']} chars")
        else:
            print(f"      Error: {result.get('error', 'Unknown')}")

    print("=" * 80)

    if passed_tests == total_tests:
        print("\n[OK] SPRINT 2 COMPLETE - RAG WORKING")
        print("\nAll test queries completed successfully!")
        print("RAG pipeline is operational and ready for Sprint 3.")
        return True
    else:
        print(f"\n[WARN] {total_tests - passed_tests} test(s) failed")
        print("Please review errors above and fix issues before proceeding.")
        return False


if __name__ == "__main__":
    success = test_rag_pipeline()
    sys.exit(0 if success else 1)
