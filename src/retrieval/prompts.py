"""
Prompt Templates for RAG Pipeline.

Contains use-case specific prompt templates:
1. SOP Assistant - Investigation steps guidance
2. Chargesheet Reviewer - Completeness checking
3. General Q&A - Legal knowledge assistant
"""

from typing import Dict


# SOP Assistant Prompt
SOP_PROMPT = """You are an AI assistant for Gujarat Police officers. Based on the following case documents from similar past cases, suggest investigation steps.

REFERENCE CASES:
{context}

CURRENT FIR DETAILS:
{query}

Provide your response as:

1. CRITICAL STEPS (must do within 24 hours):
   - Step 1: [Action] - Cite [Source]
   - Step 2: [Action] - Cite [Source]

2. IMPORTANT STEPS (within 1 week):
   - Step 1: [Action] - Cite [Source]
   - Step 2: [Action] - Cite [Source]

3. RECOMMENDED STEPS:
   - Step 1: [Action] - Cite [Source]
   - Step 2: [Action] - Cite [Source]

For each step, cite which reference case informed this recommendation.
Always mention relevant IPC/BNS sections.
Respond in English. Be specific and actionable.
"""


# Chargesheet Review Prompt
CHARGESHEET_REVIEW_PROMPT = """You are an AI legal assistant reviewing a chargesheet for Gujarat Police. Compare the draft against successful chargesheets from similar cases.

REFERENCE SUCCESSFUL CHARGESHEETS:
{context}

DRAFT CHARGESHEET TO REVIEW:
{query}

Provide:

1. COMPLETENESS SCORE: X/100
   Brief justification for the score.

2. MISSING ELEMENTS (critical gaps):
   - Element 1: [Description] - See [Source]
   - Element 2: [Description] - See [Source]

3. WEAK POINTS (areas needing strengthening):
   - Point 1: [Description] - Strengthen by [Suggestion] - See [Source]
   - Point 2: [Description] - Strengthen by [Suggestion] - See [Source]

4. STRENGTHS (well-done elements):
   - Strength 1: [Description]
   - Strength 2: [Description]

5. RECOMMENDATIONS:
   - Recommendation 1: [Specific action]
   - Recommendation 2: [Specific action]

Cite specific sections and reference cases. Be precise about what's missing.
Focus on legal completeness, evidence quality, and procedural compliance.
"""


# General Q&A Prompt
GENERAL_QA_PROMPT = """You are a legal knowledge assistant for Gujarat Police. Answer the following question using ONLY the provided source documents. Always cite your sources.

SOURCE DOCUMENTS:
{context}

QUESTION: {query}

ANSWER (cite sources for every claim):

[Provide a clear, accurate answer based on the source documents. For every fact or claim, cite the source using [Source N] format. If the sources don't contain enough information to answer the question, explicitly state that.]

SOURCES USED:
- [List the sources that were actually used in your answer]
"""


# Prompt template registry
PROMPT_TEMPLATES: Dict[str, str] = {
    "sop": SOP_PROMPT,
    "chargesheet": CHARGESHEET_REVIEW_PROMPT,
    "general": GENERAL_QA_PROMPT,
}


def get_prompt_template(use_case: str) -> str:
    """
    Get prompt template for a specific use case.

    Args:
        use_case: One of "sop", "chargesheet", or "general"

    Returns:
        Prompt template string with {context} and {query} placeholders

    Raises:
        ValueError: If use_case is not recognized
    """
    if use_case not in PROMPT_TEMPLATES:
        raise ValueError(
            f"Unknown use case: {use_case}. "
            f"Must be one of: {list(PROMPT_TEMPLATES.keys())}"
        )

    return PROMPT_TEMPLATES[use_case]


def format_prompt(use_case: str, context: str, query: str) -> str:
    """
    Format a prompt with context and query.

    Args:
        use_case: One of "sop", "chargesheet", or "general"
        context: Retrieved document context
        query: User query

    Returns:
        Formatted prompt ready for LLM
    """
    template = get_prompt_template(use_case)
    return template.format(context=context, query=query)


if __name__ == "__main__":
    # Test prompt templates
    test_context = "[Source 1: Test Case]\nSample legal text here."
    test_query = "What are the investigation steps for a theft case?"

    print("SOP Prompt:")
    print("=" * 60)
    print(format_prompt("sop", test_context, test_query))

    print("\n\nChargesheet Review Prompt:")
    print("=" * 60)
    print(format_prompt("chargesheet", test_context, "Draft chargesheet text..."))

    print("\n\nGeneral Q&A Prompt:")
    print("=" * 60)
    print(format_prompt("general", test_context, "What is Section 302 IPC?"))
