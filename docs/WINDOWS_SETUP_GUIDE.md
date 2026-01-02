# 🪟 Windows Local Testing Guide

Complete guide to test conversational memory on Windows locally.

---

## Step 1: Install Redis (Windows)

### Option A: Docker (Recommended)
```powershell
# Install Docker Desktop first: https://www.docker.com/products/docker-desktop

# Pull and run Redis
docker run -d -p 6379:6379 --name redis-haval redis:latest

# Verify
docker ps  # Should show redis container running
```

### Option B: WSL (Windows Subsystem for Linux)
```powershell
# Install WSL2
wsl --install

# Inside WSL terminal:
sudo apt-get update
sudo apt-get install redis-server
redis-server --daemonize yes

# Verify
redis-cli ping  # Should return "PONG"
```

### Option C: Native Windows Redis
```powershell
# Download from: https://github.com/tporadowski/redis/releases
# Extract and run:
cd C:\path\to\redis
.\redis-server.exe

# In another terminal, verify:
.\redis-cli.exe ping  # Should return "PONG"
```

---

## Step 2: Install Python Dependencies

```powershell
# Navigate to project
cd e:\marketing_haval\haval_marketing_tool

# Install dependencies
pip install -r requirements.txt

# Verify redis is installed
python -c "import redis; print('Redis module OK')"
```

---

## Step 3: Update app.py (Complete Integration)

Create or update your `app.py`:

```python
# app.py
import os
import uuid
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from ai.conversation_manager import get_conversation_manager
from ai.haval_pipeline import get_rag_engine

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")
CORS(app)

# Initialize conversation manager (once at startup)
conv_manager = get_conversation_manager()

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with conversational memory"""
    data = request.json
    user_query = data.get('query')
    session_id = data.get('session_id')
    thinking_mode = data.get('thinking_mode', False)
    source = data.get('source', 'pakwheels')

    # Validate input
    if not user_query:
        return jsonify({'error': 'Query is required'}), 400

    # Generate session ID for new chats
    if not session_id:
        session_id = str(uuid.uuid4())
        print(f"[API] New session created: {session_id[:8]}...")

    # Add user message to conversation history
    conv_manager.add_message(session_id, "user", user_query)

    # Get chat history (last 4 messages = 2 rounds)
    chat_history = conv_manager.get_history_for_llm(session_id)

    print(f"[API] Session: {session_id[:8]}... | Query: '{user_query[:50]}...'")
    print(f"[API] History size: {len(chat_history)} messages")

    # Get RAG engine
    rag_engine = get_rag_engine()

    # Generate response with conversational memory
    response = rag_engine.answer(
        question=user_query,
        history=chat_history,        # ← Enables intent classification + reformulation
        thinking_mode=thinking_mode,
        source=source,
        session_id=session_id         # ← Enables semantic caching
    )

    # Store assistant response in conversation history
    conv_manager.add_message(session_id, "assistant", response)

    return jsonify({
        'response': response,
        'session_id': session_id,
        'history_size': len(chat_history) + 2  # +2 for current round
    })

@app.route('/api/new_chat', methods=['POST'])
def new_chat():
    """Create new chat session"""
    session_id = str(uuid.uuid4())
    print(f"[API] New chat session: {session_id[:8]}...")
    return jsonify({'session_id': session_id})

@app.route('/api/clear_session', methods=['POST'])
def clear_session():
    """Clear conversation history for a session"""
    data = request.json
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'error': 'Session ID required'}), 400

    conv_manager.clear_session(session_id)
    return jsonify({'message': 'Session cleared', 'session_id': session_id})

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Check Redis connection
        conv_manager.get_session_stats()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"error: {str(e)}"

    return jsonify({
        'status': 'ok',
        'redis': redis_status,
        'conversational_memory': 'enabled'
    })

if __name__ == '__main__':
    print("\n" + "="*70)
    print("  Haval Marketing Tool with Conversational Memory")
    print("="*70)
    print("\nFeatures:")
    print("  ✓ Sliding window memory (last 4 messages)")
    print("  ✓ Intent classification (context-dependent vs standalone)")
    print("  ✓ Query reformulation (vague → explicit)")
    print("  ✓ Semantic caching (instant responses)")
    print("\nEndpoints:")
    print("  POST /api/chat - Main chat endpoint")
    print("  POST /api/new_chat - Create new session")
    print("  POST /api/clear_session - Clear session history")
    print("  GET /api/health - Health check")
    print("\n" + "="*70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## Step 4: Test with cURL (Windows PowerShell)

### Test 1: Health Check
```powershell
curl http://localhost:5000/api/health
# Expected: {"status": "ok", "redis": "connected", ...}
```

### Test 2: New Chat Session
```powershell
$session = (curl -Method POST http://localhost:5000/api/new_chat | ConvertFrom-Json).session_id
echo "Session ID: $session"
```

### Test 3: First Query (Standalone)
```powershell
$body = @{
    query = "Haval H6 price in Pakistan"
    session_id = $session
} | ConvertTo-Json

curl -Method POST -Uri http://localhost:5000/api/chat `
     -ContentType "application/json" `
     -Body $body
```

### Test 4: Follow-up Query (Context-Dependent)
```powershell
$body = @{
    query = "What about white ones?"
    session_id = $session
} | ConvertTo-Json

curl -Method POST -Uri http://localhost:5000/api/chat `
     -ContentType "application/json" `
     -Body $body

# Watch terminal logs for:
# [IntentClassifier] Query: 'What about white ones?' → CONTEXT_DEPENDENT
# [QueryReformulator] Reformulated: 'Haval H6 white color variant price'
```

### Test 5: "Summarize the above" (Edge Case)
```powershell
$body = @{
    query = "Summarize the above in 2 sentences"
    session_id = $session
} | ConvertTo-Json

curl -Method POST -Uri http://localhost:5000/api/chat `
     -ContentType "application/json" `
     -Body $body

# Should work because assistant response is now included (truncated)
```

---

## Step 5: Test with Python Script

Create `test_local_windows.py`:

```python
import requests
import json

BASE_URL = "http://localhost:5000"

def test_conversational_memory():
    print("\n" + "="*70)
    print("  Testing Conversational Memory on Windows")
    print("="*70 + "\n")

    # Create new session
    print("1. Creating new session...")
    resp = requests.post(f"{BASE_URL}/api/new_chat")
    session_id = resp.json()['session_id']
    print(f"   ✓ Session ID: {session_id[:16]}...\n")

    # Test 1: First query (standalone)
    print("2. First query (standalone):")
    query1 = "Haval H6 price in Pakistan"
    print(f"   Q: {query1}")

    resp = requests.post(f"{BASE_URL}/api/chat", json={
        'query': query1,
        'session_id': session_id
    })
    response1 = resp.json()['response']
    print(f"   A: {response1[:100]}...\n")

    # Test 2: Context-dependent follow-up
    print("3. Context-dependent follow-up:")
    query2 = "What about white ones?"
    print(f"   Q: {query2}")
    print(f"   Expected: Should reformulate to 'Haval H6 white color variant price'")

    resp = requests.post(f"{BASE_URL}/api/chat", json={
        'query': query2,
        'session_id': session_id
    })
    response2 = resp.json()['response']
    print(f"   A: {response2[:100]}...\n")

    # Test 3: "Summarize the above" (edge case)
    print("4. Edge case: 'Summarize the above'")
    query3 = "Summarize the above in 2 sentences"
    print(f"   Q: {query3}")
    print(f"   Expected: Should use assistant's previous response")

    resp = requests.post(f"{BASE_URL}/api/chat", json={
        'query': query3,
        'session_id': session_id
    })
    response3 = resp.json()['response']
    print(f"   A: {response3[:100]}...\n")

    # Test 4: WhatsApp user query (topic switch)
    print("5. Topic switch: WhatsApp user query")
    query4 = "Show me Ahmed's chat"
    print(f"   Q: {query4}")
    print(f"   Expected: Should NOT mix H6 context with user query")

    resp = requests.post(f"{BASE_URL}/api/chat", json={
        'query': query4,
        'session_id': session_id,
        'source': 'whatsapp'
    })
    response4 = resp.json()['response']
    print(f"   A: {response4[:100]}...\n")

    # Test 5: Semantic cache hit
    print("6. Semantic cache test:")
    query5 = "How much is the H6?"  # Similar to query1
    print(f"   Q: {query5}")
    print(f"   Expected: Cache hit (similarity > 0.96)")

    resp = requests.post(f"{BASE_URL}/api/chat", json={
        'query': query5,
        'session_id': session_id
    })
    response5 = resp.json()['response']
    print(f"   A: {response5[:100]}...\n")

    # Summary
    print("="*70)
    print("  ✅ All tests completed!")
    print("="*70)
    print("\nCheck your terminal logs for:")
    print("  - [IntentClassifier] classifications")
    print("  - [QueryReformulator] reformulations")
    print("  - [RAG] cache hits/misses")
    print("="*70 + "\n")

if __name__ == '__main__':
    try:
        test_conversational_memory()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to Flask server")
        print("   Make sure Redis is running and start Flask:")
        print("   python app.py\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
```

Run test:
```powershell
python test_local_windows.py
```

---

## Step 6: Understanding History Handling

### Example: "Summarize the above"

```python
# Full history stored in Redis
history = [
    {"role": "user", "content": "Haval H6 price in Pakistan"},
    {"role": "assistant", "content": "The Haval H6 2024 model is available in Pakistan with a starting price of PKR 9,990,000 for the base variant... [2000 tokens]"},
    {"role": "user", "content": "Summarize the above"}
]

# What intent classifier/reformulator receives (TRUNCATED):
summarized_history = """
1. User: Haval H6 price in Pakistan
2. Assistant: The Haval H6 2024 model is available in Pakistan with a starting price of PKR 9,990,000...
3. User: Summarize the above
"""

# ✓ Assistant response is included BUT truncated to first 100 chars
# ✓ LLM can now understand "the above" refers to pricing info
# ✓ Prompt size: ~150 tokens (instead of 2000+)

# Reformulation:
# Original: "Summarize the above"
# Reformulated: "Summarize Haval H6 pricing information Pakistan"
# ✓ Works correctly!
```

---

## Step 7: Run Full System (Windows)

### Terminal 1: Start Redis
```powershell
# Using Docker:
docker start redis-haval

# OR using native Redis:
cd C:\path\to\redis
.\redis-server.exe
```

### Terminal 2: Start Flask App
```powershell
cd e:\marketing_haval\haval_marketing_tool

# Set environment variables (optional)
$env:REDIS_HOST = "localhost"
$env:REDIS_PORT = "6379"

# Run Flask
python app.py
```

### Terminal 3: Run Tests
```powershell
cd e:\marketing_haval\haval_marketing_tool

# Test with Python script
python test_local_windows.py

# OR test with cURL (see Step 4)
```

---

## Step 8: Monitor Redis (Optional)

### Terminal 4: Monitor Redis
```powershell
# Using Docker:
docker exec -it redis-haval redis-cli monitor

# OR using native Redis:
.\redis-cli.exe monitor
```

You'll see operations like:
```
"SETEX" "chat:session:abc12345:history" "86400" "[{\"r\":\"u\",\"c\":\"Haval H6 price\"...}]"
"GET" "chat:session:abc12345:history"
```

---

## 🎯 What to Expect in Logs

### Intent Classification
```
[IntentClassifier] Query: 'What about white ones?' → CONTEXT_DEPENDENT
```

### Query Reformulation
```
[QueryReformulator] Original: 'What about white ones?'
[QueryReformulator] Reformulated: 'Haval H6 white color variant price Pakistan'
```

### Semantic Cache
```
[RAG] Cache miss (0.003s), proceeding with full RAG pipeline
[RAG] 💾 Stored response in semantic cache (session: abc12345...)

# Later, similar query:
[RAG] 🎯 CACHE HIT! (similarity: 0.97, 0.002s)
[RAG] Returning cached response (zero LLM cost)
```

### History Handling
```
[API] Session: abc12345... | Query: 'Summarize the above'
[API] History size: 3 messages

# Internally, history is summarized:
# 1. User: Haval H6 price
# 2. Assistant: The Haval H6 2024 model is available... (truncated)
# 3. User: Summarize the above
```

---

## 🔧 Troubleshooting

### Redis Connection Error
```powershell
# Error: ConnectionRefusedError [WinError 10061]

# Fix: Start Redis
docker start redis-haval
# OR
.\redis-server.exe
```

### Import Error
```powershell
# Error: No module named 'redis'

# Fix: Install dependencies
pip install redis
```

### Port Already in Use
```powershell
# Error: Address already in use: Port 5000

# Fix: Use different port
# In app.py: app.run(..., port=5001)
```

---

## ✅ Success Checklist

- [ ] Redis running (docker ps OR redis-cli ping returns PONG)
- [ ] Dependencies installed (pip install -r requirements.txt)
- [ ] app.py updated with conversational memory
- [ ] Flask running (python app.py)
- [ ] Health check passes (curl http://localhost:5000/api/health)
- [ ] Test script passes (python test_local_windows.py)
- [ ] Logs show intent classification + reformulation
- [ ] "Summarize the above" works correctly

---

**Your Windows setup is complete! 🚀**

Test with the Python script or cURL commands above.
