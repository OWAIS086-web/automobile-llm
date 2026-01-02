from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from collections import defaultdict
import re
from ai.models import CleanPost, ConversationBlock


# ----------------------------
# helpers
# ----------------------------

def _parse_iso_utc(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        # handles "...Z"
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt
    except Exception:
        return None


def _parse_epoch_seconds(ts: Any) -> Optional[datetime]:
    try:
        if ts is None:
            return None
        secs = int(ts)
        return datetime.fromtimestamp(secs, tz=timezone.utc)
    except Exception:
        return None


def _event_datetime(e: Dict[str, Any]) -> datetime:
    # prefer ISO created => then unix timestamp => fallback to "now" (last resort)
    dt = _parse_iso_utc(e.get("created"))
    if dt:
        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    dt = _parse_epoch_seconds(e.get("timestamp"))
    if dt:
        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    # Fallback to current time (always timezone-aware)
    return datetime.now(timezone.utc)


def _clean_text(t: Optional[str]) -> Optional[str]:
    if not t:
        return None
    t = t.replace("\r\n", "\n").strip()
    return t if t else None


def _safe_int_from_id(s: Any) -> int:
    """
    WhatsApp export ids look like Mongo ObjectId hex strings (24 chars).
    Convert to int deterministically; fallback to hash.
    """
    if isinstance(s, str):
        # hex?
        try:
            return int(s, 16)
        except Exception:
            pass
    return abs(hash(str(s)))  # deterministic per run? (python hash randomizes by default)
    # If you need cross-run stability, replace with e.g. zlib.crc32.


def _extract_contact_name(events: List[Dict[str, Any]]) -> Optional[str]:
    """
    Tries to infer contact name from ticket init event like:
    "The chat has been initialized by contact Dr. Muhammad Umer Sheikh (9232...)"
    or detailedEventDescription.agentName.
    """
    # 1) detailedEventDescription.agentName
    for e in events:
        if e.get("eventType") == "ticket":
            det = e.get("detailedEventDescription") or {}
            agent = det.get("agentName")
            if isinstance(agent, str) and agent.strip():
                # remove "(923...)" tail if present
                return re.sub(r"\s*\(\d+\)\s*$", "", agent).strip()

    # 2) parse eventDescription
    for e in events:
        desc = e.get("eventDescription")
        if isinstance(desc, str) and "initialized by contact" in desc.lower():
            # grab text after "contact" up to "(" if present
            m = re.search(r"contact\s+(.*?)(\s*\(|$)", desc, flags=re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                return name if name else None

    return None


def _extract_topic_title(events: List[Dict[str, Any]]) -> str:
    """
    Prefer:
    - ticket.topicName (e.g. "General Enquiry")
    - ticket.detailedEventDescription.flowName (e.g. "Updated Dealerships")
    """
    for e in events:
        if e.get("eventType") == "ticket" and e.get("topicName"):
            return str(e["topicName"])

    for e in events:
        if e.get("eventType") == "ticket":
            det = e.get("detailedEventDescription") or {}
            if det.get("flowName"):
                return f"Flow: {det['flowName']}"

    return "WhatsApp Conversation"


def _make_clean_post(
    *,
    thread_id: str,
    source_url: str,
    topic_title: str,
    post_number: int,
    username: str,
    dt: datetime,
    text: str,
    is_owner: Optional[bool],
    post_id_raw: Any,
) -> CleanPost:
    d = dt.date()
    iso = dt.isocalendar()
    return CleanPost(
        thread_id=thread_id,
        source_url=source_url,
        post_id=_safe_int_from_id(post_id_raw),
        post_number=post_number,
        username=username,
        created_at=dt,
        updated_at=dt,
        text=text,
        reply_to_post_number=None,
        topic_title=topic_title,
        date=d,
        week_year=iso.year,
        week_number=iso.week,
        is_owner=is_owner,
    )


def _format_flattened(posts: List[CleanPost]) -> str:
    lines: List[str] = []
    for p in posts:
        # readable, consistent, good for embeddings
        ts = p.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"[{ts}] {p.username}: {p.text}")
    return "\n".join(lines).strip()


# ----------------------------
# main function
# ----------------------------

def whatsapp_json_to_conversation_blocks(
    events: List[Dict[str, Any]],
    *,
    company_id: str = "haval",
    thread_prefix: str = "whatsapp",
    source_url_prefix: str = "whatsapp://conversation/",
) -> List[ConversationBlock]:
    """
    Convert WhatsApp-style exported JSON into your ConversationBlock dataclass.

    Rules:
    - GROUP BY PHONE NUMBER (not conversationId) - lifetime conversation per customer
    - keep only eventType == "message" AND type == "text" AND non-empty text
    - ignore ticket events in output (but we can infer topic/contact name from them)
    - 1 block per phone number; root_post = first text message chronologically
    - All messages from same phone number appended to single block (no time-based splitting)
    """
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    # Group by phone number instead of conversationId for lifetime conversation tracking
    for e in events:
        # Extract phone number - try multiple possible fields
        phone = e.get("whatsappPhoneNumber") or e.get("phone") or e.get("contactNumber")

        # Fallback to conversationId if phone not available (shouldn't happen with WATI data)
        if not phone:
            phone = e.get("conversationId")

        if phone:
            # Normalize phone number (remove spaces, dashes, etc.)
            phone_normalized = re.sub(r'[^\d+]', '', str(phone))
            grouped[phone_normalized].append(e)

    blocks: List[ConversationBlock] = []

    # Iterate over phone numbers (not conversationIds)
    for phone_number, conv_events in grouped.items():
        # Sort all events from this phone number chronologically (lifetime conversation)
        conv_events_sorted = sorted(conv_events, key=_event_datetime)

        topic_title = _extract_topic_title(conv_events_sorted)
        contact_name = _extract_contact_name(conv_events_sorted) or "Contact"

        # Filter to text messages only
        msg_events: List[Dict[str, Any]] = []
        for e in conv_events_sorted:
            if e.get("eventType") != "message":
                continue
            if e.get("type") != "text":
                continue
            txt = _clean_text(e.get("text"))
            if not txt:
                continue
            msg_events.append(e)

        if not msg_events:
            continue  # No usable text messages from this phone number

        # Use phone number as unique identifier for thread (with company_id for isolation)
        thread_id = f"{company_id}_{thread_prefix}_phone_{phone_number}"
        source_url = f"{source_url_prefix}{phone_number}"

        clean_posts: List[CleanPost] = []
        for i, e in enumerate(msg_events, start=1):
            dt = _event_datetime(e)
            owner = e.get("owner")  # True => agent/bot, False => contact

            if owner:
                username = (e.get("operatorName") or "Agent").strip()
            else:
                username = contact_name

            clean_posts.append(
                _make_clean_post(
                    thread_id=thread_id,
                    source_url=source_url,
                    topic_title=topic_title,
                    post_number=i,
                    username=username,
                    dt=dt,
                    text=_clean_text(e.get("text")) or "",
                    is_owner=bool(owner) if owner is not None else None,
                    post_id_raw=e.get("id") or f"{phone_number}:{i}",
                )
            )

        root = clean_posts[0]
        replies = clean_posts[1:]
        flattened = _format_flattened(clean_posts)

        start_dt = clean_posts[0].created_at
        end_dt = clean_posts[-1].created_at

        # Create conversation block with phone number for lifetime conversation tracking
        # Store both customer name (from root_post.username) and phone number
        block = ConversationBlock(
            block_id=f"{thread_id}:{root.post_number}",
            thread_id=thread_id,
            source_url=source_url,
            topic_title=topic_title,
            root_post=root,
            replies=replies,
            flattened_text=flattened,
            start_datetime=start_dt,
            end_datetime=end_dt,
            phone_number=phone_number,  # Store phone number for metadata filtering
        )
        blocks.append(block)

    # optional: sort blocks by their start_datetime
    blocks.sort(key=lambda b: b.start_datetime)
    return blocks
