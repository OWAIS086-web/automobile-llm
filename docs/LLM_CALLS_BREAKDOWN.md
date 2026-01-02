# LLM Calls Per Query - Complete Pipeline Breakdown

## 📊 **Summary Table**

| Scenario | Non-Thinking Mode | Thinking Mode |
|----------|-------------------|---------------|
| **First Query (No History)** | 4 calls | 6 calls |
| **Follow-up Query (Standalone)** | 5 calls | 7 calls |
| **Follow-up Query (Context-Dependent)** | 9-11 calls | 11-13 calls |
| **WhatsApp Customer Query (Direct)** | 2-3 calls | 2-3 calls |

---

## 🔍 **Detailed Breakdown by Scenario**

### **SCENARIO 1: First Query (No History)**

**Example:** User's first message: "What are the top complaints?"

#### Non-Thinking Mode:
```
1. Domain Classification                    → 1 LLM call
2. Customer Name Extraction (WhatsApp only) → 1 LLM call (optional)
3. PARALLEL EXECUTION (run simultaneously):
   - Query Optimization                     → 1 LLM call
   - Format Detection                       → 1 LLM call
   - Intent Classification                  → SKIPPED (no history)
   - Citation Check                         → SKIPPED (non-thinking)
   - Keyword Extraction                     → SKIPPED (non-thinking)
4. Final Answer Generation                  → 1 LLM call

TOTAL: 4 LLM calls (3 sequential + 2 parallel)
```

#### Thinking Mode:
```
1. Domain Classification                    → 1 LLM call
2. Customer Name Extraction (WhatsApp only) → 1 LLM call (optional)
3. PARALLEL EXECUTION:
   - Query Optimization                     → 1 LLM call
   - Format Detection                       → 1 LLM call
   - Citation Check                         → 1 LLM call ✅
   - Keyword Extraction                     → 1 LLM call ✅
   - Intent Classification                  → SKIPPED (no history)
4. Final Answer Generation                  → 1 LLM call

TOTAL: 6 LLM calls (3 sequential + 4 parallel)
```

---

### **SCENARIO 2: Follow-up Query - STANDALONE**

**Example:**
- Query 1: "What are delivery delays?"
- Query 2: "What are brake issues?" (new topic, no context needed)

#### Non-Thinking Mode:
```
1. Domain Classification                    → 1 LLM call
2. Customer Name Extraction (WhatsApp only) → 1 LLM call (optional)
3. Context Selection (NEW!)                 → 1 LLM call ✅
   → Result: TOPIC_SWITCH (0 messages selected)
4. PARALLEL EXECUTION:
   - Query Optimization                     → 1 LLM call
   - Format Detection                       → 1 LLM call
   - Intent Classification                  → 1 LLM call (uses selected_history)
   - Citation Check                         → SKIPPED (non-thinking)
   - Keyword Extraction                     → SKIPPED (non-thinking)
   → Intent Result: STANDALONE (no reformulation needed)
5. Final Answer Generation                  → 1 LLM call

TOTAL: 5 LLM calls (4 sequential + 3 parallel)
```

#### Thinking Mode:
```
1. Domain Classification                    → 1 LLM call
2. Customer Name Extraction (WhatsApp only) → 1 LLM call (optional)
3. Context Selection                        → 1 LLM call
4. PARALLEL EXECUTION:
   - Query Optimization                     → 1 LLM call
   - Format Detection                       → 1 LLM call
   - Intent Classification                  → 1 LLM call
   - Citation Check                         → 1 LLM call ✅
   - Keyword Extraction                     → 1 LLM call ✅
5. Final Answer Generation                  → 1 LLM call

TOTAL: 7 LLM calls (4 sequential + 5 parallel)
```

---

### **SCENARIO 3: Follow-up Query - CONTEXT_DEPENDENT (Data Request)**

**Example:**
- Query 1: "What are delivery delays?"
- Query 2: "give me references" (needs context + reformulation)

#### Non-Thinking Mode:
```
1. Domain Classification                    → 1 LLM call
2. Customer Name Extraction (WhatsApp only) → 1 LLM call (optional)
3. Context Selection                        → 1 LLM call
   → Result: DATA_REQUEST (2 messages selected)
4. PARALLEL EXECUTION:
   - Query Optimization                     → 1 LLM call
   - Format Detection                       → 1 LLM call
   - Intent Classification                  → 1 LLM call
   → Result: CONTEXT_DEPENDENT ✅
5. Context Compression                      → 1 LLM call ✅
6. Query Reformulation                      → 1 LLM call ✅
7. Name Extraction (Reformulated Query)     → 1 LLM call ✅ (WhatsApp, if not META_OP)
8. Keyword Extraction (Reformulated Query)  → SKIPPED (non-thinking)
9. Final Answer Generation                  → 1 LLM call

TOTAL (WhatsApp): 9 LLM calls
TOTAL (PakWheels): 8 LLM calls (no name extraction)
```

#### Thinking Mode:
```
1. Domain Classification                    → 1 LLM call
2. Customer Name Extraction (WhatsApp only) → 1 LLM call (optional)
3. Context Selection                        → 1 LLM call
4. PARALLEL EXECUTION:
   - Query Optimization                     → 1 LLM call
   - Format Detection                       → 1 LLM call
   - Intent Classification                  → 1 LLM call
   - Citation Check                         → 1 LLM call ✅
   - Keyword Extraction                     → 1 LLM call ✅
5. Context Compression                      → 1 LLM call
6. Query Reformulation                      → 1 LLM call
7. Name Extraction (Reformulated Query)     → 1 LLM call (WhatsApp, if not META_OP)
8. Keyword Extraction (Reformulated Query)  → 1 LLM call ✅
9. Final Answer Generation                  → 1 LLM call

TOTAL (WhatsApp): 13 LLM calls
TOTAL (PakWheels): 12 LLM calls
```

---

### **SCENARIO 4: Follow-up Query - META_OP**

**Example:**
- Query 1: "What are the top 10 complaints?" (Answer mentions 20 customers)
- Query 2: "summarize above in 100 words"

#### Non-Thinking Mode:
```
1. Domain Classification                    → 1 LLM call
2. Customer Name Extraction (WhatsApp only) → 1 LLM call (optional)
3. Context Selection                        → 1 LLM call
   → Result: META_OP (1 message selected - last answer only)
4. PARALLEL EXECUTION:
   - Query Optimization                     → 1 LLM call
   - Format Detection                       → 1 LLM call
   - Intent Classification                  → 1 LLM call
   → Result: CONTEXT_DEPENDENT
5. Context Compression                      → 1 LLM call
6. Query Reformulation                      → 1 LLM call
7. Name Extraction (Reformulated Query)     → SKIPPED (META_OP detected) ✅
8. Keyword Extraction (Reformulated Query)  → SKIPPED (non-thinking)
9. Final Answer Generation                  → 1 LLM call

TOTAL: 8 LLM calls (no customer routing!)
```

#### Thinking Mode:
```
1. Domain Classification                    → 1 LLM call
2. Customer Name Extraction (WhatsApp only) → 1 LLM call (optional)
3. Context Selection                        → 1 LLM call
4. PARALLEL EXECUTION:
   - Query Optimization                     → 1 LLM call
   - Format Detection                       → 1 LLM call
   - Intent Classification                  → 1 LLM call
   - Citation Check                         → 1 LLM call
   - Keyword Extraction                     → 1 LLM call
5. Context Compression                      → 1 LLM call
6. Query Reformulation                      → 1 LLM call
7. Name Extraction (Reformulated Query)     → SKIPPED (META_OP) ✅
8. Keyword Extraction (Reformulated Query)  → 1 LLM call
9. Final Answer Generation                  → 1 LLM call

TOTAL: 11 LLM calls
```

---

### **SCENARIO 5: WhatsApp Customer Query (Direct Routing)**

**Example:** "Show me Ahmed's conversation"

When customer names are detected in the ORIGINAL query, it routes directly to WhatsApp customer handlers BEFORE the main pipeline.

```
1. Domain Classification                    → 1 LLM call
2. Customer Name Extraction                 → 1 LLM call
   → Found: Ahmed (SINGLE customer)
   → ROUTES TO: _handle_whatsapp_customer_query()
   → SKIPS: All parallel tasks, reformulation, etc.
3. Final Answer Generation                  → 1 LLM call
   (inside WhatsApp customer handler)

TOTAL: 3 LLM calls (fastest path!)
```

---

## 📈 **LLM Call Flow Diagram**

```
START
  ↓
[1] Domain Classification (all queries)
  ↓
[2] Customer Name Extraction (WhatsApp only)
  ↓
  ├─ If names found → Route to WhatsApp handler → [FINAL] Answer (3 calls total) ✅
  │
  ├─ No names found → Continue to main pipeline
      ↓
     [3] Context Selection (if history exists) ← NEW!
      ↓
     [4] PARALLEL TASKS (run simultaneously):
         - Query Optimization (always)
         - Format Detection (always)
         - Intent Classification (if history)
         - Citation Check (thinking mode only)
         - Keyword Extraction (thinking mode only)
      ↓
      ├─ If STANDALONE → Skip reformulation → [FINAL] Answer
      │
      ├─ If CONTEXT_DEPENDENT → Continue
          ↓
         [5] Context Compression
          ↓
         [6] Query Reformulation
          ↓
         [7] Name Extraction on Reformulated Query (WhatsApp, not META_OP)
          ↓
         [8] Keyword Extraction on Reformulated Query (thinking mode)
          ↓
          ├─ If names found → Route to WhatsApp handler
          │
          ├─ No names → Continue to main RAG
              ↓
             [FINAL] Answer Generation
```

---

## 💰 **Cost Implications**

### **Token Costs (Approximate):**

Using GPT-4o-mini ($0.150 per 1M input tokens, $0.600 per 1M output tokens):

| Component | Avg Input Tokens | Avg Output Tokens | Cost per Call |
|-----------|------------------|-------------------|---------------|
| Domain Classification | 300 | 10 | $0.00005 |
| Context Selection | 500 | 50 | $0.00011 |
| Query Optimization | 400 | 100 | $0.00012 |
| Intent Classification | 600 | 20 | $0.00011 |
| Context Compression | 800 | 150 | $0.00021 |
| Query Reformulation | 700 | 50 | $0.00014 |
| Name Extraction | 300 | 30 | $0.00006 |
| Keyword Extraction | 400 | 50 | $0.00009 |
| Format Detection | 300 | 20 | $0.00006 |
| Citation Check | 300 | 10 | $0.00005 |
| Final Answer | 3000 | 500 | $0.00075 |

### **Per-Query Cost:**

- **First query (thinking):** ~$0.0012 (6 calls)
- **Follow-up standalone (thinking):** ~$0.0014 (7 calls)
- **Follow-up context-dependent (thinking):** ~$0.0020 (13 calls)
- **WhatsApp direct route:** ~$0.0008 (3 calls) ← Cheapest!

---

## ⚡ **Latency Implications**

### **Sequential LLM Calls:**
- Domain Classification: ~0.5s
- Customer Name Extraction: ~0.4s
- Context Selection: ~0.6s
- Context Compression: ~0.8s
- Query Reformulation: ~0.7s
- Name Extraction (reformulated): ~0.4s
- Final Answer: ~2.0s

### **Parallel LLM Calls** (run simultaneously):
- Total time = max(individual times) ≈ 1.5s

### **Total Latency:**
- **First query:** ~4.0s (2 sequential + 1.5s parallel + 2s answer)
- **Follow-up standalone:** ~4.5s (3 sequential + 1.5s parallel + 2s answer)
- **Follow-up context-dependent:** ~7.0s (5 sequential + 1.5s parallel + 2s answer)
- **WhatsApp direct:** ~3.0s (2 sequential + 2s answer) ← Fastest!

---

## 🎯 **Optimization Recommendations**

### **1. Context Selection is Worth It:**
- Adds 1 LLM call (~$0.00011, ~0.6s)
- But saves tokens in compression/reformulation
- Prevents unnecessary customer routing (saves up to 3 calls)

### **2. Parallel Execution is Critical:**
- Without it: 5-7s extra latency
- With it: Only ~1.5s (max of parallel tasks)

### **3. Early Routing Saves Everything:**
- Detecting customer names early (scenario 5) saves 10 LLM calls!
- Encourages users to be explicit: "Show Ahmed's chat" vs vague "tell me more"

### **4. META_OP Detection Saves 2-3 Calls:**
- Without: 13 calls (extracts 20 customer names, routes incorrectly)
- With: 11 calls (skips name extraction, no routing)

---

## 🔢 **Final Count Summary**

### **Maximum LLM Calls (Worst Case):**
- **13 calls**: Follow-up context-dependent query, thinking mode, WhatsApp
- Cost: ~$0.002 per query
- Latency: ~7 seconds

### **Minimum LLM Calls (Best Case):**
- **3 calls**: Direct WhatsApp customer query
- Cost: ~$0.0008 per query
- Latency: ~3 seconds

### **Average (Typical Use):**
- **7-9 calls** per query
- Cost: ~$0.0014 per query
- Latency: ~5 seconds
