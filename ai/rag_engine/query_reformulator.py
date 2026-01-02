"""
Query Reformulation Module

Rewrites context-dependent queries into standalone, search-optimized queries
using chat history for context resolution.

Optimized for ChromaDB vector retrieval with automotive domain specificity.
"""

from __future__ import annotations
from typing import List, Dict, Optional
from ai.llm_client import BaseLLMClient


def reformulate_query(
    query: str,
    chat_history: List[Dict[str, str]],
    llm: BaseLLMClient,
    company_name: str = "Haval"
) -> str:
    """
    Reformulate a context-dependent query into a standalone search query.

    Converts vague follow-ups into explicit, search-optimized queries by:
    - Resolving pronouns (it, that, ones) to specific entities
    - Carrying forward context (car models, locations, features)
    - Adding relevant keywords for better vector retrieval

    Args:
        query: User's context-dependent query
        chat_history: Recent conversation messages (last 4 messages recommended)
        llm: LLM client for reformulation
        company_name: Company name for domain-specific optimization (default: "Haval")

    Returns:
        Reformulated standalone query optimized for vector search

    Examples:
        Input:  "What about white ones?"
        History: User asked "Haval H6 price"
        Output: "Haval H6 white color variant pricing Pakistan"

        Input:  "Anything in Lahore?"
        History: User asked "Haval listings in Karachi"
        Output: "Haval car listings available in Lahore Pakistan"

        Input:  "Does it have a sunroof?"
        History: Discussing "Haval Jolion"
        Output: "Haval Jolion sunroof panoramic roof feature availability"
    """
    if not chat_history or len(chat_history) == 0:
        # No history, return original query with domain boost
        return f"{company_name} {query}"

    # Build context from chat history (with smart compression)
    # Get compression LLM from config if available
    compression_llm = None
    try:
        from config.llm_config import get_llm_for_component
        compression_llm = get_llm_for_component("context_compression", fallback_api_key=None)
    except Exception as e:
        print(f"[QueryReformulator] Warning: Could not load compression LLM: {e}")
        print(f"[QueryReformulator] Falling back to simple truncation")

    history_context = _build_reformulation_context(
        chat_history=chat_history,
        current_query=query,
        compression_llm=compression_llm
    )

    # Reformulation prompt
    reformulation_prompt = f"""You are a query reformulator for an automotive search system.

**TASK**: Rewrite the user's query into a STANDALONE, SEARCH-OPTIMIZED query that can be understood WITHOUT conversation context.

**RULES FOR REFORMULATION**:

0. **CRITICAL - Meta-Operations on Previous Answer** (HIGHEST PRIORITY):
   When user asks to OPERATE ON the previous answer itself (NOT request new data):
   → "summarize above", "elaborate", "explain more", "clarify", "give more details", "expand on this"
   → These are asking to TRANSFORM the previous answer, NOT to fetch new data
   → DO NOT include customer names from compressed context
   → Only include the TOPIC from previous answer

   Examples:
   - Previous: Answer about delivery delays (mentions 10 customers)
   - User: "summarize above in 150 words"
   - Reformulate: "delivery delays complaints summary" (NO customer names!)

   - Previous: Answer about brake issues (mentions Shariq, Ahmed, Bilal)
   - User: "elaborate on this"
   - Reformulate: "brake issues details" (NO customer names!)

   - Previous: Answer about pricing for H6
   - User: "explain more"
   - Reformulate: "H6 pricing details" (NO customer names!)

   **WHY**: Meta-operations want to transform the ANSWER, not re-query the database with all names.
   If we include all names, the system will route to customer-specific handlers instead of summarizing!

1. **Resolve Pronouns**: Replace "it", "that", "ones", "this" with actual entities from context
   - "Does it have a sunroof?" → "Haval Jolion sunroof feature"
   - "What about white ones?" → "Kia white color variant"

2. **Preserve Intent**: Keep the core question/intent from the original query
   - "What about Lahore?" (intent: location change) → "Haval listings in Lahore"
   - "And the price?" (intent: pricing) → "Kia price Pakistan"

3. **CRITICAL - Reference/Citation Requests** (High Priority):
   When user asks for "references", "sources", "citations", "examples", "proof", "evidence":
   → They want supporting data for the TOPIC just discussed
   → You MUST preserve the TOPIC from previous message
   → You MUST preserve ALL CUSTOMER NAMES mentioned in previous response

   Examples:
   - Previous: "delivery timeline quoted to customers"
   - User: "can you please provide the references?"
   - Reformulate: "Haval H6 delivery timeline references customer quotes"

   - Previous: Response mentions "Shariq, Ahmed, Usman complained about delays"
   - User: "provide references of the customers you mentioned"
   - Reformulate: "Haval H6 customer chats Shariq Ahmed Usman delivery delay references"

   - Previous: "brake problems on PakWheels"
   - User: "show me the sources"
   - Reformulate: "Haval H6 brake problems PakWheels sources citations"

4. **Carry Forward Context ONLY if Relevant**:
   - Car model name (H6, Jolion, Tank, Picanto etc.) → ONLY if discussing car features/pricing
   - Date or date range if mentioned → ONLY if discussing time-based queries
   - Customer/User name → ONLY if asking about that specific person

   **CRITICAL**: Do NOT mix contexts!
   - If user asks "Show me Ahmed's chat" after discussing H6 → DO NOT add "Haval H6" to the query
   - If user switches topic → DO NOT carry forward unrelated context
   - If user asks about location after discussing features → Replace feature context with location

5. **Optimize for Search**: Use keywords that help vector similarity matching
   - Add "Pakistan" for local queries
   - Use synonyms: "sunroof" → "sunroof panoramic roof"
   - Add context: "price" → "price cost pricing"

6. **Handle Topic Switches Intelligently**:
   - If user switches from car discussion to user chat query → DO NOT mix contexts
   - If user switches from Karachi to Lahore → REPLACE location, don't add both
   - If user switches from price to features → REPLACE topic, don't add both

7. **CRITICAL - Customer Name Preservation**:
   If previous conversation mentions customer/person names:
   → You MUST include ALL names in reformulated query
   → Look for structured format: "Names: Ahmed, Shariq, Usman"
   → Include in query: "customer chats Ahmed Shariq Usman references"
   → NEVER drop names - they are crucial for filtering!

8. **Keep it Concise**: 5-15 words max, focused on search keywords

**AUTOMOTIVE DOMAIN CONTEXT**:
- Company: {company_name}
- Common models: H6, Jolion, Tank 300, Tank 500, Picanto, Sportage etc
- Common topics: price, features, availability, listings, reviews, issues, service


**PREVIOUS CONVERSATION**:
{history_context}

**USER'S VAGUE QUERY**: "{query}"

**IMPORTANT NOTES**:
- If history contains "Names: [list]", include ALL names in reformulated query
- If user asks for "references/sources/citations", preserve topic + names from previous message
- Never drop customer names - they are used for filtering retrieval!

**YOUR REFORMULATED QUERY** (standalone, search-optimized, 5-15 words):
"""

    messages = [{"role": "user", "content": reformulation_prompt}]

    try:
        response = llm.generate(messages, max_tokens=200, temperature=0.2)
        reformulated = response.content.strip()

        # Clean up the reformulated query
        reformulated = _clean_reformulated_query(reformulated, query)

        print(f"[QueryReformulator] ✅ Reformulation successful")
        print(f"[QueryReformulator]   Original: '{query}'")
        print(f"[QueryReformulator]   Reformulated: '{reformulated}'")

        return reformulated

    except Exception as e:
        print(f"[QueryReformulator] ❌ Error during reformulation: {e}")
        # Fallback: Use original query with company name
        fallback = f"{company_name} {query}"
        print(f"[QueryReformulator]   Fallback: '{fallback}'")
        return fallback


def _build_reformulation_context(
    chat_history: List[Dict[str, str]],
    max_messages: int = 4,
    current_query: str = "",
    compression_llm: Optional[BaseLLMClient] = None
) -> str:
    """
    Build focused context for query reformulation.

    Strategy:
    - Include ALL messages (user + assistant) for context
    - Smart compression for assistant responses:
      * If compression_llm provided AND current_query has reference terms:
        → Use LLM to extract relevant portions semantically
      * Otherwise:
        → Simple truncation to first 100 chars
    - This handles "summarize the above" / "explain that" queries

    Args:
        chat_history: Recent conversation messages
        max_messages: Maximum messages to include (default: 4 = 2 rounds)
        current_query: Current user query (to extract relevant context)
        compression_llm: Optional LLM for semantic compression (GPT-4o-mini recommended)

    Returns:
        Formatted context string with smart compression
    """
    if not chat_history:
        return "No previous conversation."

    # Take last N messages (sliding window)
    recent = chat_history[-max_messages:]

    # Format all messages (user + compressed assistant)
    lines = []
    for i, msg in enumerate(recent, 1):
        role = msg["role"].capitalize()
        content = msg["content"]

        # Smart compression for assistant responses (use same logic as intent classifier)
        if role == "Assistant":
            # Import the compression function from intent_classifier
            from .intent_classifier import _compress_assistant_response
            content = _compress_assistant_response(
                response=content,
                current_query=current_query,
                compression_llm=compression_llm
            )
        else:
            # User queries: truncate only if very long
            if len(content) > 200:
                content = content[:200] + "..."

        lines.append(f"{i}. {role}: {content}")

    return "\n".join(lines)


def _clean_reformulated_query(reformulated: str, original: str) -> str:
    """
    Clean and validate reformulated query.

    Removes common LLM artifacts and ensures quality.

    Args:
        reformulated: LLM-generated reformulated query
        original: Original user query

    Returns:
        Cleaned reformulated query
    """
    # Remove quotation marks
    reformulated = reformulated.strip('"\'')

    # Remove common LLM prefixes
    prefixes_to_remove = [
        "Reformulated query:",
        "Query:",
        "Standalone query:",
        "Search query:",
        "Output:",
    ]

    for prefix in prefixes_to_remove:
        if reformulated.lower().startswith(prefix.lower()):
            reformulated = reformulated[len(prefix):].strip()
            reformulated = reformulated.lstrip(':').strip()

    # Remove trailing punctuation except question marks
    while reformulated and reformulated[-1] in ['.', ',', ';']:
        reformulated = reformulated[:-1].strip()

    # If reformulation is too short or empty, return original
    if len(reformulated) < 3:
        return original

    # If reformulation is identical to original, no need to reformulate
    if reformulated.lower() == original.lower():
        return original

    return reformulated


def extract_entities_from_history(
    chat_history: List[Dict[str, str]],
    enrichment_state=None
) -> Dict[str, Optional[str]]:
    """
    Extract key entities from chat history for context carryover.

    DYNAMIC EXTRACTION - No hardcoded models/locations.
    Uses enrichment_state variants if available, otherwise generic pattern matching.

    Args:
        chat_history: Recent conversation messages
        enrichment_state: Optional EnrichmentState with known variants/locations

    Returns:
        Dict with extracted entities (for debugging/validation only)
    """
    import re

    entities = {
        "car_model": None,
        "location": None,
        "topic": None,  # Generic topic (price, features, etc.)
    }

    # Get car models from enrichment state if available
    car_models = []
    if enrichment_state and hasattr(enrichment_state, 'known_variants'):
        car_models = list(enrichment_state.known_variants.keys())

    # Common Pakistani cities (fallback)
    common_locations = ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad"]

    # Scan recent USER messages only (reverse order = most recent first)
    for msg in reversed(chat_history):
        if msg["role"].lower() != "user":
            continue

        content = msg["content"]

        # Extract car model (from enrichment state or generic pattern)
        if not entities["car_model"] and car_models:
            for model in car_models:
                if re.search(rf'\b{model}\b', content, re.IGNORECASE):
                    entities["car_model"] = model
                    break

        # Extract location
        if not entities["location"]:
            for location in common_locations:
                if re.search(rf'\b{location}\b', content, re.IGNORECASE):
                    entities["location"] = location
                    break

        # Extract generic topic (price, features, etc.)
        if not entities["topic"]:
            topics = ["price", "features", "mileage", "fuel", "safety", "warranty", "sunroof"]
            for topic in topics:
                if re.search(rf'\b{topic}\b', content, re.IGNORECASE):
                    entities["topic"] = topic
                    break

    return entities
