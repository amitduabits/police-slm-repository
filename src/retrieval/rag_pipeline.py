"""
RAG Pipeline - End-to-end Retrieval-Augmented Generation.

Combines:
1. Vector search (embeddings)
2. Keyword search (BM25)
3. Query expansion
4. Context assembly with citations
5. LLM generation
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from src.retrieval.embeddings import EmbeddingPipeline, SearchResult
from src.model.inference import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Response from RAG pipeline."""
    query: str
    use_case: str
    response: str
    context: str
    citations: List[Dict]
    num_results: int
    metadata: Dict


class RAGPipeline:
    """
    RAG Pipeline for Gujarat Police investigation support.

    Features:
    - Hybrid search (vector + keyword)
    - Query expansion with legal terms
    - Context assembly with source citations
    - LLM generation with use-case specific prompts
    """

    def __init__(
        self,
        embedding_pipeline: Optional[EmbeddingPipeline] = None,
        llm_client: Optional[LLMClient] = None,
        max_context_tokens: int = 3000,
        vector_weight: float = 0.7
    ):
        """
        Initialize RAG pipeline.

        Args:
            embedding_pipeline: EmbeddingPipeline instance for vector search
            llm_client: LLMClient instance for generation
            max_context_tokens: Max tokens for context assembly
            vector_weight: Weight for vector search (0-1), keyword gets 1-weight
        """
        from src.retrieval.embeddings import create_embedding_pipeline
        from src.model.inference import create_llm_client

        self.embeddings = embedding_pipeline or create_embedding_pipeline()
        self.llm = llm_client or create_llm_client()
        self.max_context_tokens = max_context_tokens
        self.vector_weight = vector_weight

        logger.info("RAG Pipeline initialized")
        logger.info(f"  Embedding model: {self.embeddings.model}")
        logger.info(f"  LLM backend: {self.llm.backend}")

    def expand_query(self, query: str) -> str:
        """
        Expand query with legal synonyms and abbreviations.

        Args:
            query: Original query text

        Returns:
            Expanded query with additional terms
        """
        # Simple expansion for POC
        # Full implementation would use legal term dictionary
        expansions = {
            "murder": "murder Section 302 IPC Section 103 BNS homicide killing",
            "theft": "theft Section 379 IPC Section 303 BNS stealing larceny",
            "bail": "bail anticipatory bail regular bail Section 437 CrPC",
            "chargesheet": "chargesheet Section 173 CrPC prosecution complaint",
            "FIR": "FIR First Information Report Section 154 CrPC",
            "302": "Section 302 IPC Section 103 BNS murder",
            "304": "Section 304 IPC culpable homicide",
            "376": "Section 376 IPC Section 63 BNS rape sexual assault",
        }

        expanded = query
        for term, expansion in expansions.items():
            if term.lower() in query.lower():
                expanded = f"{expanded} {expansion}"

        logger.debug(f"Query expanded: '{query}' -> '{expanded}'")
        return expanded

    def vector_search(
        self,
        query: str,
        top_k: int = 10,
        collection: str = "all_documents",
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Vector search using embeddings.

        Args:
            query: Search query
            top_k: Number of results
            collection: ChromaDB collection name
            filters: Optional metadata filters

        Returns:
            List of search results with scores
        """
        results = self.embeddings.search(
            query=query,
            collection=collection,
            top_k=top_k,
            filter_dict=filters
        )

        # Convert SearchResult to dict
        return [
            {
                "text": r.chunk_text,
                "id": r.doc_id,
                "score": r.score,
                "metadata": r.metadata,
                "source": "vector"
            }
            for r in results
        ]

    def keyword_search(
        self,
        query: str,
        top_k: int = 10,
        collection: str = "all_documents",
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Keyword search (BM25-like).
        For POC, just returns empty list. Full implementation would use BM25.

        Args:
            query: Search query
            top_k: Number of results
            collection: Collection name
            filters: Optional filters

        Returns:
            List of keyword search results
        """
        # POC: keyword search not implemented yet
        # Full implementation would use BM25 or PostgreSQL full-text search
        logger.debug("Keyword search not implemented, returning empty results")
        return []

    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        collection: str = "all_documents",
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Hybrid search combining vector and keyword results.

        Args:
            query: Search query
            top_k: Number of results to return
            collection: Collection name
            filters: Optional metadata filters

        Returns:
            Ranked list of search results
        """
        # Expand query
        expanded = self.expand_query(query)

        # Vector search
        vector_results = self.vector_search(
            expanded,
            top_k=top_k * 2,  # Get more for merging
            collection=collection,
            filters=filters
        )

        # Keyword search
        keyword_results = self.keyword_search(
            query,
            top_k=top_k,
            collection=collection,
            filters=filters
        )

        # Merge and re-rank
        combined = {}
        for doc in vector_results:
            doc_id = doc.get("id", doc["text"][:50])
            combined[doc_id] = {**doc, "combined_score": doc["score"] * self.vector_weight}

        keyword_weight = 1 - self.vector_weight
        for doc in keyword_results:
            doc_id = doc.get("id", doc["text"][:50])
            if doc_id in combined:
                combined[doc_id]["combined_score"] += doc["score"] * keyword_weight
            else:
                combined[doc_id] = {**doc, "combined_score": doc["score"] * keyword_weight}

        # Sort by combined score
        ranked = sorted(combined.values(), key=lambda x: x["combined_score"], reverse=True)
        return ranked[:top_k]

    def assemble_context(self, results: List[Dict], max_tokens: Optional[int] = None) -> str:
        """
        Assemble retrieved chunks into context string with source citations.

        Args:
            results: List of search results
            max_tokens: Max tokens (defaults to self.max_context_tokens)

        Returns:
            Formatted context string with citations
        """
        max_tokens = max_tokens or self.max_context_tokens
        context_parts = []
        token_count = 0

        for i, r in enumerate(results):
            meta = r.get("metadata", {})
            source_tag = f"[Source {i+1}: {meta.get('title', 'Unknown')}]"
            chunk = f"{source_tag}\n{r['text']}"

            # Rough token count (words * 1.3)
            chunk_tokens = int(len(chunk.split()) * 1.3)

            if token_count + chunk_tokens > max_tokens:
                break

            context_parts.append(chunk)
            token_count += chunk_tokens

        return "\n\n---\n\n".join(context_parts)

    def query(
        self,
        text: str,
        use_case: str = "general",
        collection: str = "all_documents",
        filters: Optional[Dict] = None,
        top_k: int = 5
    ) -> RAGResponse:
        """
        Full RAG query: search -> assemble -> generate.

        Args:
            text: User query text
            use_case: "sop", "chargesheet", or "general"
            collection: ChromaDB collection to search
            filters: Optional metadata filters
            top_k: Number of chunks to retrieve

        Returns:
            RAGResponse with answer and citations
        """
        logger.info(f"RAG query: use_case={use_case}, top_k={top_k}")

        # 1. Hybrid search
        results = self.hybrid_search(
            text,
            top_k=top_k,
            collection=collection,
            filters=filters
        )

        # 2. Assemble context
        context = self.assemble_context(results)

        # 3. Build prompt based on use case
        from src.retrieval.prompts import get_prompt_template

        prompt = get_prompt_template(use_case).format(
            context=context,
            query=text
        )

        # 4. Generate response
        response_text = ""
        if self.llm and self.llm.health_check():
            try:
                response_text = self.llm.generate(
                    prompt,
                    max_tokens=2048,
                    temperature=0.1
                )
                logger.info(f"Generated response: {len(response_text)} chars")
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                response_text = f"[LLM Error: {str(e)}] Retrieved {len(results)} relevant documents."
        else:
            logger.warning("LLM not available, returning retrieved context only")
            response_text = f"[LLM unavailable] Retrieved {len(results)} relevant documents. See citations below."

        # 5. Extract citations
        citations = [
            {
                "source": r.get("metadata", {}).get("title", "Unknown"),
                "doc_type": r.get("metadata", {}).get("doc_type", ""),
                "court": r.get("metadata", {}).get("court", ""),
                "score": r.get("combined_score", r.get("score", 0)),
            }
            for r in results
        ]

        return RAGResponse(
            query=text,
            use_case=use_case,
            response=response_text,
            context=context,
            citations=citations,
            num_results=len(results),
            metadata={
                "vector_weight": self.vector_weight,
                "max_context_tokens": self.max_context_tokens,
            }
        )


def create_rag_pipeline(
    embedding_pipeline: Optional[EmbeddingPipeline] = None,
    llm_client: Optional[LLMClient] = None
) -> RAGPipeline:
    """Factory function to create a RAG pipeline."""
    return RAGPipeline(
        embedding_pipeline=embedding_pipeline,
        llm_client=llm_client
    )


if __name__ == "__main__":
    # Test the pipeline
    logging.basicConfig(level=logging.INFO)

    rag = create_rag_pipeline()
    result = rag.query(
        "What is the punishment for murder under Section 302 IPC?",
        use_case="general",
        top_k=3
    )

    print(f"\nQuery: {result.query}")
    print(f"Response: {result.response[:500]}")
    print(f"\nCitations ({len(result.citations)}):")
    for c in result.citations:
        print(f"  - {c['source']} (score: {c['score']:.3f})")
