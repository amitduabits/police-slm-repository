"""
SOP Routes - Investigation guidance based on similar past cases.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_user, get_rag_pipeline
from src.api.models import User, SearchHistory
from src.api.schemas import SOPRequest, SOPResponse, Citation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sop", tags=["SOP Assistant"])


@router.post("/suggest", response_model=SOPResponse)
async def suggest_investigation_steps(
    request: SOPRequest,
    current_user: User = Depends(get_current_user),
    rag_pipeline: Any = Depends(get_rag_pipeline),
    db: AsyncSession = Depends(get_db)
):
    """
    Suggest investigation steps based on FIR details.

    Uses RAG pipeline to find similar past cases and generate
    prioritized investigation guidance.

    Args:
        request: SOPRequest with FIR details and case category
        current_user: Authenticated user
        rag_pipeline: RAG pipeline instance
        db: Database session

    Returns:
        SOPResponse with AI-generated investigation steps and citations
    """
    logger.info(f"SOP request from user {current_user.username}: {request.fir_details[:100]}...")

    start_time = time.time()

    try:
        # Build query for RAG
        query_parts = [request.fir_details]
        if request.case_category:
            query_parts.append(f"Category: {request.case_category}")
        if request.sections_cited:
            query_parts.append(f"Sections: {', '.join(request.sections_cited)}")

        query = " | ".join(query_parts)

        # Build metadata filters
        filters = {}
        if request.district:
            filters["district"] = request.district

        # Query RAG pipeline
        result = rag_pipeline.query(
            text=query,
            use_case="sop",
            filters=filters if filters else None,
            top_k=request.top_k
        )

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Convert citations
        citations = [
            Citation(
                source=c.get("source", "Unknown"),
                doc_type=c.get("doc_type"),
                court=c.get("court"),
                score=c.get("score", 0.0)
            )
            for c in result.citations
        ]

        # Log to search history
        search_entry = SearchHistory(
            user_id=current_user.id,
            query=query,
            filters=str(filters),
            results_count=result.num_results,
            response_time_ms=processing_time_ms
        )
        db.add(search_entry)
        await db.commit()

        logger.info(
            f"SOP suggestion completed for {current_user.username}: "
            f"{result.num_results} results, {processing_time_ms}ms"
        )

        return SOPResponse(
            query=query,
            response=result.response,
            citations=citations,
            num_results=result.num_results,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"SOP suggestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate investigation guidance: {str(e)}"
        )
