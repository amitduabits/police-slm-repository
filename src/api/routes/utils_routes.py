"""
Utils Routes - Utility endpoints like section conversion.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_current_user, get_section_normalizer
from src.api.models import User
from src.api.schemas import SectionConvertResponse, SectionMapping

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/utils", tags=["Utilities"])


@router.get("/convert-section/{section}", response_model=SectionConvertResponse)
async def convert_section(
    section: str,
    from_code: str = Query(..., pattern="^(IPC|BNS|CrPC|BNSS|IEA|BSA)$"),
    to_code: str = Query(..., pattern="^(IPC|BNS|CrPC|BNSS|IEA|BSA)$"),
    current_user: User = Depends(get_current_user),
    normalizer: Any = Depends(get_section_normalizer)
):
    """
    Convert section number between old and new legal codes.

    Converts:
    - IPC ↔ BNS (Bharatiya Nyaya Sanhita)
    - CrPC ↔ BNSS (Bharatiya Nagarik Suraksha Sanhita)
    - IEA ↔ BSA (Bharatiya Sakshya Adhiniyam)

    Args:
        section: Section number (e.g., "302", "376")
        from_code: Source code (IPC, BNS, CrPC, BNSS, IEA, BSA)
        to_code: Target code (IPC, BNS, CrPC, BNSS, IEA, BSA)
        current_user: Authenticated user
        normalizer: SectionNormalizer instance

    Returns:
        SectionConvertResponse with mapping details

    Example:
        GET /utils/convert-section/302?from_code=IPC&to_code=BNS
        Returns Section 103 BNS (Murder)
    """
    logger.info(f"Section conversion request: {section} from {from_code} to {to_code}")

    try:
        # Build section identifier
        section_id = f"Section {section} {from_code}"

        # Use normalizer to get mapping
        mapping_result = normalizer.get_mapping(from_code, section, to_code)

        if not mapping_result:
            return SectionConvertResponse(
                query=f"{section} {from_code} → {to_code}",
                mapping=None,
                message=f"No mapping found for {section_id} to {to_code}"
            )

        # Build SectionMapping response
        section_mapping = SectionMapping(
            old_code=mapping_result.get("old_code", from_code),
            old_section=mapping_result.get("old_section", section),
            old_title=mapping_result.get("old_title"),
            new_code=mapping_result.get("new_code", to_code),
            new_section=mapping_result.get("new_section"),
            new_title=mapping_result.get("new_title"),
            description=mapping_result.get("description"),
            is_decriminalized=mapping_result.get("is_decriminalized", False)
        )

        message = f"{section_id} maps to Section {section_mapping.new_section} {to_code}"
        if section_mapping.is_decriminalized:
            message += " (DECRIMINALIZED)"

        return SectionConvertResponse(
            query=f"{section} {from_code} → {to_code}",
            mapping=section_mapping,
            message=message
        )

    except Exception as e:
        logger.error(f"Section conversion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Section conversion failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint (no authentication required).

    Returns basic system status.
    """
    return {
        "status": "healthy",
        "service": "Gujarat Police SLM API",
        "version": "0.1.0"
    }
