"""
Search Routes - Document search and retrieval.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_user, get_rag_pipeline
from src.api.models import User, SearchHistory
from src.api.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SimilarCasesRequest,
    FiltersResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/query", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    rag_pipeline: Any = Depends(get_rag_pipeline),
    db: AsyncSession = Depends(get_db)
):
    """
    Natural language search across all documents.

    Args:
        request: SearchRequest with query and filters
        current_user: Authenticated user
        rag_pipeline: RAG pipeline instance
        db: Database session

    Returns:
        SearchResponse with relevant results
    """
    logger.info(f"Search request from {current_user.username}: {request.query}")

    start_time = time.time()

    try:
        # Use RAG pipeline's hybrid search
        result = rag_pipeline.query(
            text=request.query,
            use_case="general",
            collection=request.collection,
            filters=request.filters if request.filters else None,
            top_k=request.top_k
        )

        # Convert to SearchResultItem format
        search_results = []
        for i, citation in enumerate(result.citations):
            # Extract metadata from citation
            search_results.append(SearchResultItem(
                id=str(i),  # TODO: Use actual document ID
                title=citation.get("source", "Unknown"),
                snippet=result.context.split("---")[i][:500] if i < len(result.context.split("---")) else "",
                document_type=citation.get("doc_type", "unknown"),
                source=citation.get("source", "unknown"),
                court=citation.get("court"),
                date_published=None,  # TODO: Extract from metadata
                sections_cited=[],  # TODO: Extract from metadata
                score=citation.get("score", 0.0),
                url=None
            ))

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Log to search history
        search_entry = SearchHistory(
            user_id=current_user.id,
            query=request.query,
            filters=str(request.filters),
            results_count=len(search_results),
            top_result_id=search_results[0].id if search_results else None,
            response_time_ms=processing_time_ms
        )
        db.add(search_entry)
        await db.commit()

        logger.info(
            f"Search completed for {current_user.username}: "
            f"{len(search_results)} results, {processing_time_ms}ms"
        )

        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            processing_time_ms=processing_time_ms,
            filters_applied=request.filters or {}
        )

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/similar", response_model=SearchResponse)
async def find_similar_cases(
    request: SimilarCasesRequest,
    current_user: User = Depends(get_current_user),
    rag_pipeline: Any = Depends(get_rag_pipeline),
    db: AsyncSession = Depends(get_db)
):
    """
    Find similar cases by document ID.

    Uses the specified document as a query to find similar documents.

    Args:
        request: SimilarCasesRequest with document_id
        current_user: Authenticated user
        rag_pipeline: RAG pipeline instance
        db: Database session

    Returns:
        SearchResponse with similar cases
    """
    logger.info(f"Similar cases request from {current_user.username}: doc_id={request.document_id}")

    # TODO: Implement similar document search
    # For POC, return empty results
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Similar cases search not yet implemented"
    )


@router.get("/filters", response_model=FiltersResponse)
async def get_available_filters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get available filter options for search.

    Returns lists of available document types, courts, districts, etc.
    that can be used to filter search results.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        FiltersResponse with available filter options
    """
    logger.info(f"Filters request from {current_user.username}")

    try:
        from sqlalchemy import select, func
        from src.api.models import Document

        # Get unique document types
        doc_types_result = await db.execute(
            select(Document.document_type).distinct().order_by(Document.document_type)
        )
        document_types = [row[0] for row in doc_types_result.all() if row[0]]

        # Get unique sources
        sources_result = await db.execute(
            select(Document.source).distinct().order_by(Document.source)
        )
        sources = [row[0] for row in sources_result.all() if row[0]]

        # Get unique courts
        courts_result = await db.execute(
            select(Document.court).distinct().order_by(Document.court)
        )
        courts = [row[0] for row in courts_result.all() if row[0]]

        # Get unique districts
        districts_result = await db.execute(
            select(Document.district).distinct().order_by(Document.district)
        )
        districts = [row[0] for row in districts_result.all() if row[0]]

        # Get available years from date_published
        years_result = await db.execute(
            select(func.extract('year', Document.date_published)).distinct()
        )
        years = sorted([int(row[0]) for row in years_result.all() if row[0]], reverse=True)

        return FiltersResponse(
            document_types=document_types,
            sources=sources,
            courts=courts,
            districts=districts,
            years=years
        )

    except Exception as e:
        logger.error(f"Failed to get filters: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve filters: {str(e)}"
        )
