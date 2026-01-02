# ai/haval_pipeline.py
from __future__ import annotations

import logging
import traceback
from threading import Thread, Lock
from pathlib import Path
from typing import Any, Dict, Optional, List
import os
import pickle
import json
from dotenv import load_dotenv

load_dotenv()

from ai.io_utils import load_raw_posts_from_json
from ai.text_cleaning import raw_to_clean_posts
from ai.reply_merge import group_posts_into_conversation_blocks
from ai.time_analytics import compute_daily_stats, compute_weekly_stats
from ai.embeddings import SentenceTransformerEmbedder
from ai.vector_store import ChromaVectorStore
from ai.llm_client import GeminiClient, GrokClient
from ai.rag_engine import RAGEngine
from ai.enrichment import (
    classify_blocks,
    compute_enrichment_metrics,
    EnrichmentMetrics,
    EnrichmentState,
)
from config import get_llm_for_component

from ai.utils.whatsapp_data import whatsapp_json_to_conversation_blocks
from ai.utils.facebook_data import facebook_posts_to_conversation_blocks

logger = logging.getLogger(__name__)

# NEW: backend-only toggle (no UI)
ENABLE_ENRICHMENT = os.getenv("HAVAL_ENABLE_ENRICHMENT", "1").lower() in (
    "1",
    "true",
    "yes",
    "on",
)

_enrichment_state = EnrichmentState()


_status_lock = Lock()

# Internal global state for this demo
_pipeline_status: Dict[str, Any] = {
    "status": "idle",       # idle | processing | enriching | indexing | separating_mixed_blocks | ready | failed
    "error": None,
    "topic_url": None,
    "json_path": None,
    "total_posts": 0,
    "total_blocks": 0,
    "enrichment_metrics": None,
    "current_step": None,
}

_rag_engine: Optional[RAGEngine] = None
_blocks: List[Any] = []
_daily_stats: List[Any] = []
_weekly_stats: List[Any] = []
_chat_history: Dict[str, List[Dict[str, str]]] = {}

# Multi-company support: Store vector stores per company
_company_vector_stores: Dict[str, Dict[str, ChromaVectorStore]] = {}
_company_rag_engines: Dict[str, RAGEngine] = {}

# Default paths for Haval (backward compatibility)
pakwheels_persist_path = "data/chroma_pakwheels"
whatsapp_persist_path = "data/chroma_whatsapp"
Path(pakwheels_persist_path).mkdir(parents=True, exist_ok=True)
Path(whatsapp_persist_path).mkdir(parents=True, exist_ok=True)
Path("data").mkdir(parents=True, exist_ok=True)

STATE_FILE = Path("data") / "haval_h6_pipeline_state.pkl"

# Global embedder (shared across all companies)
embedder = SentenceTransformerEmbedder()
print("[HavalPipeline] Embedder initialized.")

# Initialize default Haval vector stores (backward compatibility)
pakwheels_vs = ChromaVectorStore(
    persist_path=pakwheels_persist_path,
    collection_name="pakwheels_blocks",
    embedder=embedder,
    blocks_file="data/pakwheels_blocks.pkl",
)

whatsapp_vs = ChromaVectorStore(
    persist_path=whatsapp_persist_path,
    collection_name="whatsapp_blocks",
    embedder=embedder,
    blocks_file="data/whatsapp_blocks.pkl",
)

# Register Haval stores
_company_vector_stores["haval"] = {
    "pakwheels": pakwheels_vs,
    "whatsapp": whatsapp_vs,
}


def get_or_create_vector_store(company_id: str, source_type: str) -> Optional[ChromaVectorStore]:
    """
    Get or create a vector store for a specific company and source type.

    Args:
        company_id: Company identifier (e.g., "haval", "kia", "toyota")
        source_type: Source type ("pakwheels" or "whatsapp")

    Returns:
        ChromaVectorStore instance or None if not applicable
    """
    try:
        from config import get_company_config
        config = get_company_config(company_id)
    except Exception as e:
        logger.error(f"Failed to get company config for {company_id}: {e}")
        return None

    # Check if company already has this vector store initialized
    if company_id in _company_vector_stores:
        if source_type in _company_vector_stores[company_id]:
            return _company_vector_stores[company_id][source_type]

    # Validate that the source is available for this company
    if source_type == "pakwheels" and not config.has_pakwheels:
        return None
    if source_type == "whatsapp" and not config.has_whatsapp:
        return None

    # Get paths from config
    if source_type == "pakwheels":
        persist_path = config.chroma_pakwheels_path
        blocks_file = config.pakwheels_blocks_file
        collection_name = f"{company_id}_pakwheels_blocks"
    elif source_type == "whatsapp":
        persist_path = config.chroma_whatsapp_path
        blocks_file = config.whatsapp_blocks_file
        collection_name = f"{company_id}_whatsapp_blocks"
    else:
        logger.error(f"Unknown source type: {source_type}")
        return None

    if not persist_path or not blocks_file:
        return None

    # Create directory if it doesn't exist
    Path(persist_path).mkdir(parents=True, exist_ok=True)

    # Create vector store
    try:
        vs = ChromaVectorStore(
            persist_path=persist_path,
            collection_name=collection_name,
            embedder=embedder,
            blocks_file=blocks_file,
        )

        # Register in cache
        if company_id not in _company_vector_stores:
            _company_vector_stores[company_id] = {}
        _company_vector_stores[company_id][source_type] = vs

        logger.info(f"[HavalPipeline] Created vector store for {company_id}/{source_type}")
        return vs
    except Exception as e:
        logger.error(f"Failed to create vector store for {company_id}/{source_type}: {e}")
        return None


def get_vector_store_for_company(company_id: str, source_type: str) -> Optional[ChromaVectorStore]:
    """
    Get vector store for a specific company and source.
    Public API for external use.
    """
    return get_or_create_vector_store(company_id, source_type)


# ---------------------------------------------------------------------------
# Persistence helpers (save / restore pipeline state)
# ---------------------------------------------------------------------------

def _save_pipeline_state(
    blocks: List[Any],
    daily_stats: List[Any],
    weekly_stats: List[Any],
    pipeline_status: Dict[str, Any],
) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "blocks": blocks,
            "daily_stats": daily_stats,
            "weekly_stats": weekly_stats,
            # Only store a shallow copy so we don't hang on to live references
            "pipeline_status": dict(pipeline_status),
            "enrichment_state": _enrichment_state,
        }
        with STATE_FILE.open("wb") as f:
            pickle.dump(snapshot, f)
        logger.info("[HavalPipeline] Saved pipeline state to %s", STATE_FILE)
    except Exception:
        logger.exception("[HavalPipeline] Failed to save pipeline state")


def _restore_pipeline_state_if_exists() -> None:
    """
    On module import / app start, try to restore a previously completed pipeline.

    This will:
    - Reload blocks, daily_stats, weekly_stats.
    - Rebuild vs.blocks_by_id.
    - Recreate the RAG engine with the current LLM (Grok preferred, fallback Gemini).
    - Mark the pipeline as 'ready' so chat & analytics are available out of the box.
    """
    global _rag_engine, _blocks, _daily_stats, _weekly_stats, _enrichment_state

    if not STATE_FILE.exists():
        logger.info("[HavalPipeline] No saved pipeline state found at %s", STATE_FILE)
        return

    try:
        with STATE_FILE.open("rb") as f:
            snapshot = pickle.load(f)
    except Exception:
        logger.exception("[HavalPipeline] Failed to load pipeline state from %s", STATE_FILE)
        return

    blocks = snapshot.get("blocks") or []
    daily_stats = snapshot.get("daily_stats") or []
    weekly_stats = snapshot.get("weekly_stats") or []
    saved_status = snapshot.get("pipeline_status") or {}
    enrichment_state = snapshot.get("enrichment_state") or EnrichmentState()

    _blocks = blocks
    _daily_stats = daily_stats
    _weekly_stats = weekly_stats
    _enrichment_state = _enrichment_state.set_prev_state(enrichment_state)

    # Rebuild in-memory mapping for the vector store so retrieval has full blocks
    # IMPORTANT: Only add blocks to their respective vector store based on block_id prefix
    try:
        for b in blocks:
            # Route blocks to correct vector store based on block_id prefix
            if "pakwheels" in b.block_id.lower():
                pakwheels_vs.blocks_by_id[b.block_id] = b
            elif "whatsapp" in b.block_id.lower():
                whatsapp_vs.blocks_by_id[b.block_id] = b
            else:
                # Unknown block type - log warning but don't fail
                logger.warning(f"[HavalPipeline] Unknown block type during restore: {b.block_id}")

    except Exception:
        logger.exception("[HavalPipeline] Failed to rebuild blocks_by_id from snapshot")

    # Restore pipeline status (but make sure we're not stuck in a running state)
    with _status_lock:
        _pipeline_status.update(saved_status)
        if blocks and _pipeline_status.get("status") not in (
            "processing",
            "enriching",
            "indexing",
            "separating_mixed_blocks",
            "failed",
        ):
            _pipeline_status["status"] = "ready"
        _pipeline_status["current_step"] = "ready"

    # Re-create LLM and RAG engine on top of existing Chroma store
    try:
        from os import getenv

        # Initialize LLM from centralized config
        logger.info("[HavalPipeline] Restoring RAG engine with configured LLM.")
        api_key = getenv("GEMINI_API_KEY", "AIzaSyBAbDTiaRTCNouLSiBU-beJPCij357RgUk")
        llm = get_llm_for_component("answer_generation", fallback_api_key=api_key)

        _rag_engine = RAGEngine(pakwheels_store=pakwheels_vs, whatsapp_store=whatsapp_vs, llm=llm, k=5)

        logger.info(
            "[HavalPipeline] Restored pipeline state from disk. "
            "Blocks=%d, daily_stats=%d, weekly_stats=%d",
            len(blocks),
            len(daily_stats),
            len(weekly_stats),
        )
    except Exception:
        logger.exception("[HavalPipeline] Failed to reinitialise RAG engine from snapshot")


# Try to restore any existing state immediately on import
_restore_pipeline_state_if_exists()


# ---------- Public helpers used by Flask ----------

def get_pipeline_status() -> Dict[str, Any]:
    """
    Return a JSON-serializable snapshot of the current pipeline state.
    """
    with _status_lock:
        status_copy = dict(_pipeline_status)
        metrics: Optional[EnrichmentMetrics] = _pipeline_status.get("enrichment_metrics")
        if metrics is not None:
            status_copy["enrichment_metrics"] = {
                "total_blocks": metrics.total_blocks,
                "status_counts": metrics.status_counts,
                "variant_counts": metrics.variant_counts,
                "sentiment_counts": metrics.sentiment_counts,
                "tag_counts": metrics.tag_counts,
            }
        else:
            status_copy["enrichment_metrics"] = None
        return status_copy


def get_rag_engine(company_id: str = "haval") -> Optional[RAGEngine]:
    """
    Return the ready RAG engine for a specific company.

    Args:
        company_id: Company identifier (e.g., "haval", "kia", "toyota")

    Returns:
        RAGEngine instance for the company, or None if not initialized
    """
    # Try to get company-specific RAG engine first
    if company_id in _company_rag_engines:
        return _company_rag_engines[company_id]

    # Fallback to global _rag_engine for backward compatibility (Haval only)
    if company_id == "haval":
        return _rag_engine

    # Try to create RAG engine on-the-fly if vector stores exist
    try:
        from os import getenv

        pakwheels_vs = get_or_create_vector_store(company_id, "pakwheels")
        whatsapp_vs = get_or_create_vector_store(company_id, "whatsapp")

        # Only create if at least one vector store exists and has data
        if pakwheels_vs or whatsapp_vs:
            # Initialize LLM from centralized config
            api_key = getenv("GEMINI_API_KEY", "AIzaSyBAbDTiaRTCNouLSiBU-beJPCij357RgUk")
            llm = get_llm_for_component("answer_generation", fallback_api_key=api_key)

            rag = RAGEngine(
                pakwheels_store=pakwheels_vs,
                whatsapp_store=whatsapp_vs,
                llm=llm,
                k=5,
                company_id=company_id  # Pass company_id for correct prompts/citations
            )
            _company_rag_engines[company_id] = rag
            logger.info(f"[HavalPipeline] Created RAG engine on-demand for {company_id}")
            return rag
    except Exception as e:
        logger.error(f"Failed to create RAG engine for {company_id}: {e}")

    return None


def get_chat_history(mode) -> List[Dict[str, str]]:
    """
    Return the current in-memory chat history for the Haval chatbot.
    """
    return _chat_history.get(mode, [])

def append_to_chat_history(query: str, answer: str, mode: str) -> None:
    """
    Append a message to the in-memory chat history for the Haval chatbot.
    """
    if mode not in _chat_history:
        _chat_history[mode] = []
    _chat_history[mode].append({"role": "user", "content": query})
    _chat_history[mode].append({"role": "assistant", "content": answer})


def start_haval_pipeline(
    json_path: str,
    topic_url: str,
    persist_dir: Optional[str] = None,
    sources: str = "Pakwheels",
    company_id: str = "haval"
) -> None:
    """
    Kick off the full pipeline in a background thread for any company.

    - Non-blocking: returns immediately.
    - If a pipeline is already running, it will not start a second one.
    - After successful completion, state is persisted so future restarts can
      reload blocks + RAG directly from disk without scraping again.

    Args:
        json_path: Path to scraped JSON data file
        topic_url: PakWheels thread URL
        persist_dir: Optional custom persist directory (deprecated)
        sources: Data source type ("Pakwheels", "Whatsapp", "Facebook")
        company_id: Company identifier (e.g., "haval", "kia", "toyota")
    """
    with _status_lock:
        if _pipeline_status["status"] in ("processing", "enriching", "indexing", "separating_mixed_blocks"):
            logger.info(f"{company_id.title()} pipeline already running; skipping new start.")
            return

        _pipeline_status.update(
            {
                "status": "processing",
                "error": None,
                "topic_url": topic_url,
                "json_path": json_path,
                "total_posts": 0,
                "total_blocks": 0,
                "enrichment_metrics": None,
                "current_step": "load_posts",
                "company_id": company_id,
            }
        )

    t = Thread(
        target=_run_pipeline,
        args=(json_path, topic_url, sources, company_id),
        daemon=True,
    )
    t.start()


# ---------- Internal worker ----------

def _run_mix_block_separation(company_id: str = "haval") -> None:
    """
    Run the mix_block.py logic to separate mixed blocks between PakWheels and WhatsApp vector stores.
    This is automatically called after the pipeline completes successfully.

    Args:
        company_id: Company identifier to use company-specific paths
    """
    import pickle
    import os
    from datetime import datetime
    from config import get_company_config

    # Get company-specific paths from config
    try:
        config = get_company_config(company_id)
        pakwheels_pkl = config.pakwheels_blocks_file
        whatsapp_pkl = config.whatsapp_blocks_file if config.has_whatsapp else None
    except Exception as e:
        logger.error(f"[MixBlock] Failed to get company config for {company_id}: {e}")
        # Fallback to Haval defaults for backward compatibility
        pakwheels_pkl = "data/pakwheels_blocks.pkl"
        whatsapp_pkl = "data/whatsapp_blocks.pkl"

    print(f"[MixBlock] Starting block separation for {company_id}...")
    print(f"[MixBlock]   PakWheels pkl: {pakwheels_pkl}")
    if whatsapp_pkl:
        print(f"[MixBlock]   WhatsApp pkl: {whatsapp_pkl}")
    else:
        print(f"[MixBlock]   WhatsApp: Not available for {company_id}")

    # Load both pkl files
    pakwheels_blocks = {}
    whatsapp_blocks = {}

    if os.path.exists(pakwheels_pkl):
        with open(pakwheels_pkl, 'rb') as f:
            pakwheels_blocks = pickle.load(f)
        print(f"[MixBlock] Loaded {len(pakwheels_blocks)} blocks from PakWheels pkl")
    else:
        print(f"[MixBlock] PakWheels pkl not found")

    # Only try to load WhatsApp pkl if it's configured for this company
    if whatsapp_pkl and os.path.exists(whatsapp_pkl):
        with open(whatsapp_pkl, 'rb') as f:
            whatsapp_blocks = pickle.load(f)
        print(f"[MixBlock] Loaded {len(whatsapp_blocks)} blocks from WhatsApp pkl")
    elif whatsapp_pkl:
        print(f"[MixBlock] WhatsApp pkl not found (expected for first run)")
    # else: WhatsApp not configured for this company, skip

    # If both files are empty or don't exist, nothing to separate
    if not pakwheels_blocks and not whatsapp_blocks:
        print("[MixBlock] No blocks to separate, skipping...")
        return

    # Separate blocks based on block_id prefix
    pakwheels_only = {}
    whatsapp_only = {}

    print("[MixBlock] Separating blocks...")

    # Get company-specific thread_id prefix for PakWheels blocks
    pakwheels_prefix = f"{config.pakwheels_thread_id}:"
    whatsapp_prefix = "whatsapp_"

    # Process PakWheels pkl
    for block_id, block in pakwheels_blocks.items():
        if "pakwheels" in block_id.lower():
            # Any PakWheels block (any company, any naming convention)
            pakwheels_only[block_id] = block
        elif block_id.startswith(whatsapp_prefix):
            if whatsapp_pkl:  # Only separate WhatsApp if configured
                print(f"[MixBlock] Found WhatsApp block in PakWheels pkl: {block_id}")
                whatsapp_only[block_id] = block
            else:
                print(f"[MixBlock] ⚠️  WhatsApp block found but WhatsApp not configured for {company_id}: {block_id}")
        else:
            print(f"[MixBlock] ⚠️  Unknown block type: {block_id}")

    # Process WhatsApp pkl (only if configured for this company)
    if whatsapp_pkl:
        for block_id, block in whatsapp_blocks.items():
            if block_id.startswith(whatsapp_prefix):
                if block_id not in whatsapp_only:  # Avoid duplicates
                    whatsapp_only[block_id] = block
            elif "pakwheels" in block_id.lower():
                # Check for ANY PakWheels block (from any company, any naming convention)
                # Handles: haval_h6_pakwheels:123, pakwheels_blocks_kia:456, etc.
                print(f"[MixBlock] Found PakWheels block in WhatsApp pkl: {block_id}")
                if block_id not in pakwheels_only:  # Avoid duplicates
                    pakwheels_only[block_id] = block
            else:
                print(f"[MixBlock] ⚠️  Unknown block type: {block_id}")

    print(f"[MixBlock] Results:")
    print(f"[MixBlock]   PakWheels blocks: {len(pakwheels_only)}")
    print(f"[MixBlock]   WhatsApp blocks: {len(whatsapp_only)}")

    # Only proceed if there's actual separation needed
    original_pw_count = len([bid for bid in pakwheels_blocks.keys() if bid.startswith(pakwheels_prefix)])
    original_wa_count = len([bid for bid in whatsapp_blocks.keys() if bid.startswith(whatsapp_prefix)]) if whatsapp_pkl else 0

    if len(pakwheels_only) == original_pw_count and len(whatsapp_only) == original_wa_count:
        print("[MixBlock] Blocks are already properly separated, no changes needed.")
        return

    # Backup originals
    if os.path.exists(pakwheels_pkl):
        backup = pakwheels_pkl + ".mixed_backup"
        if not os.path.exists(backup):  # Don't overwrite existing backup
            os.rename(pakwheels_pkl, backup)
            print(f"[MixBlock] Backed up PakWheels pkl to: {backup}")

    # Only backup WhatsApp if configured for this company
    if whatsapp_pkl and os.path.exists(whatsapp_pkl):
        backup = whatsapp_pkl + ".mixed_backup"
        if not os.path.exists(backup):  # Don't overwrite existing backup
            os.rename(whatsapp_pkl, backup)
            print(f"[MixBlock] Backed up WhatsApp pkl to: {backup}")

    # Save separated blocks
    print(f"[MixBlock] Saving separated blocks...")
    with open(pakwheels_pkl, 'wb') as f:
        pickle.dump(pakwheels_only, f)
    print(f"[MixBlock] ✅ Saved {len(pakwheels_only)} PakWheels blocks to {pakwheels_pkl}")

    # Only save WhatsApp blocks if configured for this company
    if whatsapp_pkl:
        with open(whatsapp_pkl, 'wb') as f:
            pickle.dump(whatsapp_only, f)
        print(f"[MixBlock] ✅ Saved {len(whatsapp_only)} WhatsApp blocks to {whatsapp_pkl}")
    else:
        print(f"[MixBlock] ⏭️  Skipped WhatsApp save (not configured for {company_id})")

    # Show date ranges
    print(f"[MixBlock] 📅 Date ranges:")

    # PakWheels range
    if pakwheels_only:
        pw_dates = []
        for block in pakwheels_only.values():
            start_dt = getattr(block, "start_datetime", None)
            end_dt = getattr(block, "end_datetime", None)
            if start_dt:
                if isinstance(start_dt, str):
                    try:
                        start_dt = datetime.fromisoformat(start_dt)
                    except:
                        pass
                if isinstance(start_dt, datetime):
                    pw_dates.append(start_dt)
            if end_dt:
                if isinstance(end_dt, str):
                    try:
                        end_dt = datetime.fromisoformat(end_dt)
                    except:
                        pass
                if isinstance(end_dt, datetime):
                    pw_dates.append(end_dt)
        if pw_dates:
            print(f"[MixBlock]   PakWheels: {min(pw_dates).strftime('%Y-%m-%d')} to {max(pw_dates).strftime('%Y-%m-%d')}")

    # WhatsApp range
    if whatsapp_only:
        wa_dates = []
        for block in whatsapp_only.values():
            start_dt = getattr(block, "start_datetime", None)
            end_dt = getattr(block, "end_datetime", None)
            if start_dt:
                if isinstance(start_dt, str):
                    try:
                        start_dt = datetime.fromisoformat(start_dt)
                    except:
                        pass
                if isinstance(start_dt, datetime):
                    wa_dates.append(start_dt)
            if end_dt:
                if isinstance(end_dt, str):
                    try:
                        end_dt = datetime.fromisoformat(end_dt)
                    except:
                        pass
                if isinstance(end_dt, datetime):
                    wa_dates.append(end_dt)
        if wa_dates:
            print(f"[MixBlock]   WhatsApp: {min(wa_dates).strftime('%Y-%m-%d')} to {max(wa_dates).strftime('%Y-%m-%d')}")

    print("[MixBlock] ✅ Block separation completed!")


def _run_pipeline(json_path: str, topic_url: str, sources: str, company_id: str = "haval") -> None:
    global _rag_engine, _blocks, _daily_stats, _weekly_stats, _enrichment_state

    try:
        from os import getenv
        from config import get_company_config

        config = get_company_config(company_id)
        thread_id = config.pakwheels_thread_id

        logger.info(f"[{config.name}Pipeline] Starting pipeline for {topic_url}, json={json_path}")
        print(f"[{config.name}Pipeline] Starting pipeline for {topic_url}, json={json_path}")

        if sources == "Pakwheels":
            # Step 1: load raw posts from JSON file
            with _status_lock:
                _pipeline_status["status"] = "processing"
                _pipeline_status["current_step"] = "load_posts"

            raw_posts = load_raw_posts_from_json(json_path)

            # Step 2: cleaning + normalization
            with _status_lock:
                _pipeline_status["current_step"] = "clean_posts"

            clean_posts = raw_to_clean_posts(raw_posts, thread_id=thread_id)

            print(f"[{config.name}Pipeline] Loaded {len(raw_posts)} raw posts, cleaned to {len(clean_posts)} posts.")

            # Step 3: merge replies into conversation blocks
            with _status_lock:
                _pipeline_status["current_step"] = "group_blocks"

            blocks = group_posts_into_conversation_blocks(clean_posts)

            print(f"[HavalPipeline] Grouped into {len(blocks)} conversation blocks.")

            daily_stats = compute_daily_stats(clean_posts)
            weekly_stats = compute_weekly_stats(clean_posts)

            print(f"[HavalPipeline] Processed {len(clean_posts)} posts into {len(blocks)} blocks.")
            print(f"[HavalPipeline] Daily stats: {daily_stats}")
            print(f"[HavalPipeline] Weekly stats: {weekly_stats}")

        elif sources == "Whatsapp":
            with _status_lock:
                _pipeline_status["status"] = "processing"
                _pipeline_status["current_step"] = "load_posts"

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            with _status_lock:
                _pipeline_status["current_step"] = "group_blocks"

            blocks = whatsapp_json_to_conversation_blocks(data, company_id=company_id)
            print(f"[{config.name}Pipeline] Grouped into {len(blocks)} conversation blocks.")

        elif sources == "Facebook":
            with _status_lock:
                _pipeline_status["status"] = "processing"
                _pipeline_status["current_step"] = "load_posts"

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            with _status_lock:
                _pipeline_status["current_step"] = "group_blocks"

            blocks = facebook_posts_to_conversation_blocks(data)
            print(f"[HavalPipeline] Grouped into {len(blocks)} conversation blocks.")

        print(f"[HavalPipeline] Enrichment enabled: {ENABLE_ENRICHMENT}")

        with _status_lock:
            _pipeline_status["total_posts"] = len(clean_posts) if sources == "Pakwheels" else 0
            _pipeline_status["total_blocks"] = len(blocks)
            _pipeline_status["status"] = "enriching" if ENABLE_ENRICHMENT else "indexing"
            _pipeline_status["current_step"] = (
                "enrichment" if ENABLE_ENRICHMENT else "indexing_embeddings"
            )

        # Initialize LLM for enrichment from centralized config
        api_key = getenv("GEMINI_API_KEY", "AIzaSyBAbDTiaRTCNouLSiBU-beJPCij357RgUk")
        print("[HavalPipeline] Initializing LLM for enrichment from centralized config.")
        llm = get_llm_for_component("enrichment", fallback_api_key=api_key)

        # Step 4 (optional): Enrichment (classification / sentiments / tags)
        if ENABLE_ENRICHMENT:
            print(f"[{config.name}Pipeline] Starting enrichment (classification / sentiment / tags)...")
            print(f"  📊 Company: {config.full_name} (ID: {company_id})")
            print(f"  📂 Data Source: {sources}")
            results = classify_blocks(
                blocks,
                llm,
                _enrichment_state,
                log_progress=True,
                company_id=company_id,
                data_source=sources.lower(),
            )
            metrics = compute_enrichment_metrics(results)
            print(f"[{config.name}Pipeline] Enrichment complete.")
            state = _enrichment_state

            with _status_lock:
                _pipeline_status["enrichment_metrics"] = metrics
                _pipeline_status["status"] = "indexing"
                _pipeline_status["current_step"] = "indexing_embeddings"
        else:
            metrics = None  # type: ignore[assignment]
            results = None
            state = None

        # Step 5: Check for existing blocks and filter out duplicates
        print(f"[{config.name}Pipeline] Checking for existing blocks to avoid duplicates...")

        # Select the appropriate vector store based on data source (company-aware)
        if sources == "Whatsapp":
            target_vs = get_or_create_vector_store(company_id, "whatsapp")
            target_persist_path = config.chroma_whatsapp_path
        else:  # Pakwheels or Facebook
            target_vs = get_or_create_vector_store(company_id, "pakwheels")
            target_persist_path = config.chroma_pakwheels_path

        if target_vs is None:
            raise RuntimeError(f"Could not create vector store for {company_id}/{sources}")


        # Filter out blocks that already exist
        existing_block_ids = set(target_vs.blocks_by_id.keys())
        new_blocks = []
        skipped_blocks = []
        
        for block in blocks:
            if block.block_id in existing_block_ids:
                skipped_blocks.append(block)
            else:
                new_blocks.append(block)
        
        print(f"[HavalPipeline] Found {len(blocks)} total blocks")
        print(f"[HavalPipeline] Skipping {len(skipped_blocks)} existing blocks")
        print(f"[HavalPipeline] Processing {len(new_blocks)} new blocks")
        
        if len(new_blocks) == 0:
            print("[HavalPipeline] No new blocks to process. Pipeline complete.")
            with _status_lock:
                _pipeline_status["status"] = "ready"
                _pipeline_status["current_step"] = "ready"
            return

        # Update blocks list to only include new blocks
        blocks = new_blocks
        
        # Update enrichment results to match new blocks if enrichment was done
        if ENABLE_ENRICHMENT and results:
            # Filter enrichment results to match new blocks
            new_results = {}
            for block in new_blocks:
                if block.block_id in results:
                    new_results[block.block_id] = results[block.block_id]
            results = new_results

        # Step 6: Embeddings + local Chroma vector store
        print("[HavalPipeline] Starting embeddings and indexing...")
        print(f"[HavalPipeline] Creating Chroma vector store at {target_persist_path}")
        print(f"[HavalPipeline] Starting embeddings and indexing for {len(blocks)} new blocks...")

        with _status_lock:
            _pipeline_status["current_step"] = "indexing_embeddings"

        target_vs.index_blocks(blocks, classification_results=results)

        print("[HavalPipeline] Indexing complete.")


        print(f"[{config.name}Pipeline] Initializing RAG engine (LLM + vector store)...")

        with _status_lock:
            _pipeline_status["current_step"] = "init_rag"

        # Get company-specific vector stores for RAG engine
        company_pakwheels_vs = get_or_create_vector_store(company_id, "pakwheels")
        company_whatsapp_vs = get_or_create_vector_store(company_id, "whatsapp")

        rag = RAGEngine(
            pakwheels_store=company_pakwheels_vs,
            whatsapp_store=company_whatsapp_vs,
            llm=llm,
            k=5,
            state=state,
            company_id=company_id  # Pass company_id for correct prompts/citations
        )

        # Store RAG engine for this company
        _company_rag_engines[company_id] = rag

        # Step 7: Save in global state
        _blocks = blocks
        _daily_stats = daily_stats if sources == "Pakwheels" else []
        _weekly_stats = weekly_stats if sources == "Pakwheels" else []
        _rag_engine = rag
        _enrichment_state = state if state is not None else _enrichment_state

        with _status_lock:
            _pipeline_status["status"] = "ready"
            _pipeline_status["current_step"] = "ready"

            # Take a snapshot of status for persistence
            status_snapshot = dict(_pipeline_status)

        # Persist pipeline snapshot so next server start can reload directly
        _save_pipeline_state(blocks, _daily_stats, _weekly_stats, status_snapshot)

        # Step 8: Auto-run mix_block.py to separate mixed blocks
        with _status_lock:
            _pipeline_status["current_step"] = "separating_mixed_blocks"
        
        print(f"[{config.name}Pipeline] Running block separation (mix_block.py)...")
        try:
            _run_mix_block_separation(company_id=company_id)
            print(f"[{config.name}Pipeline] Block separation completed successfully.")

            # Refresh date spans in RAG engine after new data is added
            if company_id in _company_rag_engines:
                print(f"[{config.name}Pipeline] Refreshing date spans in RAG engine...")
                _company_rag_engines[company_id].refresh_date_spans()
            else:
                print(f"[{config.name}Pipeline] Note: RAG engine not yet initialized, date spans will load on first query.")
        except Exception as mix_error:
            print(f"[{config.name}Pipeline] WARNING: Block separation failed: {mix_error}")
            logger.warning(f"[HavalPipeline] Block separation failed: {mix_error}")
            # Don't fail the entire pipeline for this, just log the warning

        print("[HavalPipeline] Pipeline completed successfully.")
        logger.info("[HavalPipeline] Pipeline completed successfully.")

    except Exception as e:
        print(f"[HavalPipeline] ERROR in pipeline: {e}")
        traceback.print_exc()
        logger.error("[HavalPipeline] Pipeline failed", exc_info=True)
        with _status_lock:
            _pipeline_status["status"] = "failed"
            _pipeline_status["current_step"] = "error"
            _pipeline_status["error"] = f"{e}"


def get_daily_weekly_stats():
    """
    Return (daily_stats, weekly_stats) from the last Haval pipeline run.

    These are whatever objects your time_analytics functions returned
    (typically lists of dicts or small dataclasses). For the Jinja template
    we just iterate over them.

    If the pipeline was restored from disk, these will reflect the last
    successful run prior to server restart.
    """
    with _status_lock:
        return _daily_stats, _weekly_stats
