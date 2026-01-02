# Production Conversational Memory System

**Status:** ✅ Fully Integrated
**Version:** 1.0
**Last Updated:** December 2024

---

## 📋 Overview

A production-grade conversational memory and retrieval system designed for automotive marketing tools. Provides context-aware query understanding with zero-cost semantic caching.

### Key Features

- **Sliding Window Memory**: Last 4 messages (2 conversation rounds)
- **Intent Classification**: Auto-detects context-dependent vs standalone queries
- **Query Reformulation**: Rewrites vague queries using conversation history
- **Semantic Caching**: 0.96 similarity threshold for instant responses
- **Redis-Backed**: Shared across Gunicorn workers, auto-cleanup
- **Production-Ready**: Robust error handling, comprehensive logging

---

## 🏗️ Architecture

```
User Query
│
├─> [STEP 1] Semantic Cache Check (0-5ms)
│   └─> Cache Hit? → Return cached response (ZERO LLM COST)
│
├─> [STEP 2] Intent Classification (parallel, 300-500ms)
│   ├─> Standalone: Use query as-is
│   └─> Context-Dependent: Reformulate with history
│
├─> [STEP 3] Domain Classification (existing)
│   └─> Filter out-of-domain queries
│
├─> [STEP 4] Parallel LLM Calls (existing)
│   ├─> Query Optimization
│   ├─> Citation Check
│   └─> Keyword Extraction
│
├─> [STEP 5] RAG Retrieval & Response Generation
│
└─> [STEP 6] Store in Semantic Cache (for future queries)
```

---

## 🚀 Quick Start

### 1. Install Redis

**On Linux (TensorDock):**
```bash
./setup_redis.sh
```

**Manual Installation:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify
redis-cli ping  # Should return "PONG"
```

### 2. Update Your Code

**Example: Using ConversationManager**

```python
from ai.conversation_manager import get_conversation_manager
from ai.rag_engine import RAGEngine
import uuid

# Initialize conversation manager
conv_manager = get_conversation_manager()

# Generate session ID for new chat
session_id = str(uuid.uuid4())

# User's first query
user_query = "Haval H6 price in Pakistan"

# Add to chat history
conv_manager.add_message(session_id, "user", user_query)

# Get history for RAG
chat_history = conv_manager.get_history_for_llm(session_id)

# Call RAG with session ID
response = rag_engine.answer(
    question=user_query,
    history=chat_history,
    thinking_mode=False,
    source="pakwheels",
    session_id=session_id  # NEW: Enable semantic caching
)

# Store assistant response
conv_manager.add_message(session_id, "assistant", response)

print(response)
```

**Example: Follow-up Query (Context-Dependent)**

```python
# User's follow-up query (context-dependent)
followup_query = "What about white ones?"  # Pronoun "ones" → context-dependent

# Add to history
conv_manager.add_message(session_id, "user", followup_query)

# Get updated history (last 4 messages automatically)
chat_history = conv_manager.get_history_for_llm(session_id)

# RAG will automatically:
# 1. Classify as context-dependent
# 2. Reformulate to "Haval H6 white color variant price Pakistan"
# 3. Retrieve with reformulated query
response = rag_engine.answer(
    question=followup_query,
    history=chat_history,
    thinking_mode=False,
    source="pakwheels",
    session_id=session_id
)

conv_manager.add_message(session_id, "assistant", response)

print(response)
```

---

## 🔍 How It Works: Automotive Scenarios

### Scenario A: "What about white ones?"

```
User History:
  User: "Haval H6 price in Pakistan"
  AI: "H6 starts at PKR 9.99M..."

Current Query: "What about white ones?"

Processing:
  1. Cache miss (new query)
  2. Intent: CONTEXT-DEPENDENT (pronoun "ones")
  3. Reformulated: "Haval H6 white color variant price Pakistan"
  4. ChromaDB retrieval with reformulated query
  5. Response generated
  6. Stored in cache for 24 hours

Result: User gets accurate answer about H6 white variant pricing
```

### Scenario B: "Anything in Lahore?"

```
User History:
  User: "Haval listings in Karachi"
  AI: "Found 12 H6 listings in Karachi..."

Current Query: "Anything in Lahore?"

Processing:
  1. Cache miss
  2. Intent: CONTEXT-DEPENDENT ("Anything" is vague)
  3. Reformulated: "Haval car listings available in Lahore Pakistan"
  4. Location REPLACED (Karachi → Lahore)
  5. Response generated

Result: Listings in Lahore (not Karachi)
```

### Scenario C: "Does it have a sunroof?"

```
User History:
  User: "Tell me about Haval Jolion"
  AI: "Jolion is a compact SUV..."

Current Query: "Does it have a sunroof?"

Processing:
  1. Cache miss
  2. Intent: CONTEXT-DEPENDENT (pronoun "it")
  3. Reformulated: "Haval Jolion sunroof panoramic roof feature availability"
  4. Retrieved Jolion specs
  5. Response generated

Result: Accurate answer about Jolion sunroof
```

### Scenario D: Semantic Cache Hit

```
User (Session 1): "Haval H6 price in Pakistan"
AI: [Generates response]
  → Stored in cache with similarity threshold 0.96

User (Session 1, 10 mins later): "How much is the H6 in Pakistan?"
  1. Cache check: Similarity = 0.97 > 0.96 ✅
  2. Returns cached response (0ms latency, ZERO LLM cost)

Result: Instant response, zero cost
```

---

## 📊 Logging & Debugging

### Understanding the Logs

```
======================================================================
[RAG] Query: 'What about white ones?'
[RAG] Mode: Non-Thinking | Source: pakwheels | Company: Haval H6
[RAG] Session: a7b2c3d4... | Cache: Enabled
======================================================================
[RAG] Cache miss (0.003s), proceeding with full RAG pipeline
[RAG] Domain classification: IN_DOMAIN (0.45s)
  ✅ [Parallel] optimization completed
  ✅ [Parallel] intent_classification completed
[RAG] 🔄 Query reformulated (0.52s)
[RAG]   Original: 'What about white ones?'
[RAG]   Reformulated: 'Haval H6 white color variant price Pakistan'
[RAG] Parallel tasks: Optimization + Intent Classification (1.12s)
[RAG] Using answer_generation_non_thinking: temp=0.4, max_tokens=2048
[RAG] Final answer generated (2.34s)
[RAG] 💾 Stored response in semantic cache (session: a7b2c3d4...)
======================================================================
[RAG] TOTAL TIME: 4.56s
  - Domain classification: 0.45s
  - Parallel tasks: 1.12s
  - Final answer generation: 2.34s
======================================================================
```

### Log Indicators

| Icon/Text | Meaning |
|-----------|---------|
| `🎯 CACHE HIT!` | Query matched cached response (instant, zero cost) |
| `🔄 Query reformulated` | Context-dependent query was rewritten |
| `✅ Standalone query` | No reformulation needed |
| `💾 Stored response in cache` | Response cached for future queries |
| `❌ MISS` | No cache match, proceeding with full pipeline |

---

## ⚙️ Configuration

### Redis Configuration

**Environment Variables:**
```bash
# .env file
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Optional, leave empty if no auth
REDIS_DB=0       # Default database
```

**Memory Settings:**
```bash
# Adjust in /etc/redis/redis.conf
maxmemory 256mb                    # Memory limit
maxmemory-policy allkeys-lru       # Evict oldest sessions first
```

### Semantic Cache Settings

```python
# In ai/rag_engine/core.py
self.semantic_cache = SemanticCache(
    persist_directory=f"./data/semantic_cache_{company_id}",
    similarity_threshold=0.96,    # Adjust for stricter/looser matching
    session_ttl_hours=24,          # Session cache TTL
)
```

**Similarity Threshold Guide:**
- `0.98+`: Very strict (almost exact matches only)
- `0.96`: Recommended (catches rephrased questions)
- `0.90-0.95`: Looser (may return slightly different queries)

---

## 🧪 Testing

### Test Script

Create `test_conversational_memory.py`:

```python
import uuid
from ai.conversation_manager import get_conversation_manager
from ai.rag_engine import get_rag_engine

# Initialize
conv_manager = get_conversation_manager()
rag_engine = get_rag_engine()
session_id = str(uuid.uuid4())

# Test Scenario A: Vague Follow-up
print("=== Scenario A: Vague Follow-up ===\n")

# First query
q1 = "Haval H6 price in Pakistan"
conv_manager.add_message(session_id, "user", q1)
history = conv_manager.get_history_for_llm(session_id)

r1 = rag_engine.answer(q1, history=history, session_id=session_id)
conv_manager.add_message(session_id, "assistant", r1)
print(f"Q: {q1}\nA: {r1[:200]}...\n")

# Follow-up (context-dependent)
q2 = "What about white ones?"
conv_manager.add_message(session_id, "user", q2)
history = conv_manager.get_history_for_llm(session_id)

r2 = rag_engine.answer(q2, history=history, session_id=session_id)
conv_manager.add_message(session_id, "assistant", r2)
print(f"Q: {q2}\nA: {r2[:200]}...\n")

# Test Scenario B: Semantic Cache
print("=== Scenario B: Semantic Cache ===\n")

# Same query again (should hit cache)
q3 = "How much is the H6?"
history = conv_manager.get_history_for_llm(session_id)

r3 = rag_engine.answer(q3, history=history, session_id=session_id)
print(f"Q: {q3}\nA: {r3[:200]}...\n")

# Check cache stats
cache_stats = rag_engine.semantic_cache.get_cache_stats()
session_stats = conv_manager.get_session_stats()

print("Cache Stats:", cache_stats)
print("Session Stats:", session_stats)
```

Run test:
```bash
python test_conversational_memory.py
```

---

## 🔧 Troubleshooting

### Redis Connection Failed

**Error:**
```
[ConversationManager] CRITICAL: Redis connection failed
```

**Solution:**
```bash
# Check if Redis is running
sudo systemctl status redis-server

# Start Redis
sudo systemctl start redis-server

# Verify connection
redis-cli ping
```

### High Memory Usage

**Check Redis memory:**
```bash
redis-cli info memory
```

**Clear old sessions:**
```bash
redis-cli --scan --pattern "chat:session:*" | xargs redis-cli del
```

**Adjust maxmemory:**
```bash
sudo nano /etc/redis/redis.conf
# Change: maxmemory 256mb → maxmemory 512mb
sudo systemctl restart redis-server
```

### Semantic Cache Not Working

**Check ChromaDB directory:**
```bash
ls -lh data/semantic_cache_haval/
```

**Clear cache:**
```python
from ai.rag_engine.semantic_cache import get_semantic_cache

cache = get_semantic_cache()
cache.cleanup_expired_sessions()  # Remove expired entries
```

---

## 📈 Performance Metrics

### Expected Performance

| Operation | Latency | Cost |
|-----------|---------|------|
| Cache Hit | 1-5ms | $0 |
| Intent Classification | 300-500ms | ~$0.0001 |
| Query Reformulation | 400-600ms | ~$0.0002 |
| Full RAG Pipeline | 3-6s | ~$0.005 |

### Memory Usage

| Component | Memory |
|-----------|--------|
| Redis (100 sessions × 4 msgs) | ~200KB |
| Semantic Cache (500 entries) | ~2MB |
| Total Overhead | ~2-3MB |

---

## 🎯 Best Practices

### Session Management

```python
# Generate session ID on "New Chat"
session_id = str(uuid.uuid4())

# Clear session when user starts new chat
conv_manager.clear_session(session_id)

# Monitor active sessions
active = conv_manager.get_active_sessions()
print(f"Active sessions: {len(active)}")
```

### Error Handling

```python
try:
    response = rag_engine.answer(
        question=query,
        history=history,
        session_id=session_id
    )
except Exception as e:
    # Fallback: No history, no cache
    response = rag_engine.answer(
        question=query,
        history=None,
        session_id=None
    )
    print(f"Fallback mode: {e}")
```

### Production Deployment

1. **Monitor Redis:**
   ```bash
   redis-cli monitor  # Watch commands in real-time
   ```

2. **Set up log rotation:**
   ```bash
   # /etc/logrotate.d/redis
   /var/log/redis/*.log {
       daily
       rotate 7
       compress
   }
   ```

3. **Enable Redis persistence:**
   ```bash
   # Already configured by setup_redis.sh
   save 900 1     # Save after 15min if ≥1 change
   save 300 10    # Save after 5min if ≥10 changes
   ```

---

## 📚 API Reference

### ConversationManager

```python
from ai.conversation_manager import ConversationManager, get_conversation_manager

# Initialize
manager = get_conversation_manager()

# Add message
manager.add_message(session_id, role="user", content="query")

# Get history (last 4 messages)
history = manager.get_history(session_id)  # List[Message]
llm_history = manager.get_history_for_llm(session_id)  # List[Dict]

# Clear session
manager.clear_session(session_id)

# Stats
stats = manager.get_session_stats()
```

### RAGEngine (Updated)

```python
from ai.rag_engine import RAGEngine

# Call with session_id for caching
response = rag_engine.answer(
    question=str,
    history=Optional[List[Dict]],  # Last 4 messages recommended
    thinking_mode=bool,
    source=Optional[str],
    session_id=Optional[str]  # NEW: Enable caching
)
```

---

## 🚀 What's Next?

Your production conversational memory system is ready! It will:

✅ Remember context (last 4 messages)
✅ Reformulate vague queries automatically
✅ Cache responses for zero-cost instant answers
✅ Handle topic switches gracefully
✅ Work across all Gunicorn workers

**Demo it to companies and watch them be impressed! 🎉**
