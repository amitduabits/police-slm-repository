"""
Chargesheet Routes - Chargesheet completeness review.
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
    ChargesheetReviewRequest,
    ChargesheetReviewResponse,
    Citation
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chargesheet", tags=["Chargesheet Review"])


@router.post("/review", response_model=ChargesheetReviewResponse)
async def review_chargesheet(
    request: ChargesheetReviewRequest,
    current_user: User = Depends(get_current_user),
    rag_pipeline: Any = Depends(get_rag_pipeline),
    db: AsyncSession = Depends(get_db)
):
    """
    Review chargesheet for completeness and quality.

    Compares the draft chargesheet against successful similar cases
    and identifies missing elements, weak points, and provides recommendations.

    Args:
        request: ChargesheetReviewRequest with chargesheet text
        current_user: Authenticated user
        rag_pipeline: RAG pipeline instance
        db: Database session

    Returns:
        ChargesheetReviewResponse with completeness score and issues
    """
    logger.info(f"Chargesheet review request from user {current_user.username}")

    # Validate input
    if not request.chargesheet_text and not request.chargesheet_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either chargesheet_text or chargesheet_url must be provided"
        )

    start_time = time.time()

    try:
        # Build query for RAG
        query_parts = []

        if request.chargesheet_text:
            # Use provided text (limit to reasonable size)
            chargesheet_text = request.chargesheet_text[:5000]
            query_parts.append(chargesheet_text)
        else:
            # TODO: Fetch from URL
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="URL-based chargesheet review not yet implemented"
            )

        if request.case_number:
            query_parts.append(f"Case: {request.case_number}")
        if request.sections_charged:
            query_parts.append(f"Sections: {', '.join(request.sections_charged)}")

        query = " | ".join(query_parts)

        # Query RAG pipeline with chargesheet use case
        result = rag_pipeline.query(
            text=query,
            use_case="chargesheet",
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

        # Parse response for structured fields
        # For POC, use simple parsing. Full implementation would use better NLP.
        response_text = result.response

        # Extract completeness score from response
        completeness_score = 0.0
        if "COMPLETENESS SCORE:" in response_text:
            try:
                score_line = [line for line in response_text.split("\n") if "COMPLETENESS SCORE:" in line][0]
                score_str = score_line.split(":")[1].strip().split("/")[0]
                completeness_score = float(score_str)
            except:
                logger.warning("Could not parse completeness score from response")

        # Extract missing elements, weak points, etc.
        missing_elements = []
        weak_points = []
        strengths = []
        recommendations = []

        # Simple extraction based on section headings
        # Full implementation would use better parsing
        if "MISSING ELEMENTS" in response_text:
            section = response_text.split("MISSING ELEMENTS")[1].split("\n\n")[0]
            missing_elements = [line.strip("- ").strip() for line in section.split("\n") if line.strip().startswith("-")]

        if "WEAK POINTS" in response_text:
            section = response_text.split("WEAK POINTS")[1].split("\n\n")[0]
            weak_points = [line.strip("- ").strip() for line in section.split("\n") if line.strip().startswith("-")]

        if "STRENGTHS" in response_text:
            section = response_text.split("STRENGTHS")[1].split("\n\n")[0]
            strengths = [line.strip("- ").strip() for line in section.split("\n") if line.strip().startswith("-")]

        if "RECOMMENDATIONS" in response_text:
            section = response_text.split("RECOMMENDATIONS")[1].split("\n\n")[0]
            recommendations = [line.strip("- ").strip() for line in section.split("\n") if line.strip().startswith("-")]

        # Log to search history
        search_entry = SearchHistory(
            user_id=current_user.id,
            query=f"Chargesheet review: {request.case_number or 'N/A'}",
            results_count=result.num_results,
            response_time_ms=processing_time_ms
        )
        db.add(search_entry)
        await db.commit()

        logger.info(
            f"Chargesheet review completed for {current_user.username}: "
            f"score={completeness_score}, {processing_time_ms}ms"
        )

        return ChargesheetReviewResponse(
            query=query[:200],  # Truncate for response
            completeness_score=completeness_score,
            response=response_text,
            missing_elements=missing_elements,
            weak_points=weak_points,
            strengths=strengths,
            recommendations=recommendations,
            citations=citations,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Chargesheet review failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review chargesheet: {str(e)}"
        )
