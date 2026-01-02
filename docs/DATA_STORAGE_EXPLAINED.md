# Data Storage Layers - Explained

## 📊 Three Storage Layers

Your system has **3 distinct storage layers**, each serving a different purpose:

```
Raw JSON → Processed Blocks → Vector Embeddings
   ↓              ↓                  ↓
 .json          .pkl              Chroma DB
```

---

## 1️⃣ **JSON Files** (Raw Scraped Data)

### **What Gets Saved**:
- **Raw posts** directly from data sources (PakWheels, WhatsApp, etc.)
- Unprocessed, original format

### **Format**:
```json
{
  "posts": [
    {
      "post_number": 1234,
      "username": "john_doe",
      "created_at": "2025-01-15T10:30:00+05:00",
      "cooked": "<p>This is the actual post text with HTML...</p>",
      "avatar_template": "/user_avatar/...",
      "user_title": "Member",
      ...
    },
    {
      "post_number": 1235,
      "username": "jane_smith",
      ...
    }
  ]
}
```

### **File Naming**:
```
PakWheels:
  data/featured_research__Haval H6 Dedicated Discussion.json
  data/featured_research__Kia Lucky Motors Pakistan.json

WhatsApp:
  data/all_messages.json
  data/WATI_Full_Conversations.json
```

### **When Used**:
- ✅ **Input to pipeline** - First step, loads raw data
- ✅ **Scraping stage** - Created by scraper script
- ✅ **Re-processing** - Can rerun pipeline from scratch using same JSON
- ❌ **NOT used during queries** - Too slow, not searchable

### **Purpose**:
- **Source of truth** - Original unmodified data
- **Backup** - Can always regenerate blocks from JSON
- **Debugging** - See what was actually scraped

---

## 2️⃣ **PKL Files** (Processed Conversation Blocks)

### **What Gets Saved**:
- **ConversationBlock objects** - Python dataclass objects
- Posts grouped into conversations (root + replies)
- Cleaned, normalized, structured data
- **Optional**: Enrichment metadata (variant, sentiment, tags, summary)

### **Format** (Python pickle - binary):
```python
{
  "haval_h6_pakwheels:post_1234": ConversationBlock(
      block_id="haval_h6_pakwheels:post_1234",
      thread_id="haval_h6_pakwheels",
      source_url="https://pakwheels.com/forums/...",
      topic_title="Haval H6 Dedicated Discussion",

      root_post=CleanPost(
          post_number=1234,
          username="john_doe",
          created_at=datetime(2025, 1, 15, 10, 30),
          text="What is the fuel economy of H6?",
          ...
      ),

      replies=[
          CleanPost(post_number=1235, text="Around 12-14 km/l..."),
          CleanPost(post_number=1236, text="I get 13 km/l..."),
      ],

      flattened_text="""
          Post by john_doe (2025-01-15):
          What is the fuel economy of H6?

          Reply by jane_smith:
          Around 12-14 km/l in city...

          Reply by bob_lee:
          I get 13 km/l...
      """,

      start_datetime=datetime(2025, 1, 15, 10, 30),
      end_datetime=datetime(2025, 1, 15, 14, 20),

      # Enrichment metadata (if enabled)
      variant="H6 PHEV",
      sentiment="positive",
      tags=["fuel_economy", "performance"],
      summary="Discussion about H6 fuel efficiency...",
      complaint_type=None,
      is_complaint=False,
  ),

  "haval_h6_pakwheels:post_5678": ConversationBlock(...),
  ...
}
```

### **File Naming**:
```
PakWheels Blocks:
  data/pakwheels_blocks_haval.pkl
  data/pakwheels_blocks_kia.pkl
  data/pakwheels_blocks_toyota.pkl

WhatsApp Blocks:
  data/whatsapp_blocks_haval.pkl
  data/whatsapp_blocks_kia.pkl
```

### **When Used**:
- ✅ **After pipeline processing** - Created from JSON
- ✅ **During enrichment** - LLM adds metadata to blocks
- ✅ **During indexing** - Loaded to create Chroma embeddings
- ✅ **During queries** - RAG engine retrieves full block objects
- ✅ **State restoration** - App loads blocks on startup
- ✅ **Analytics** - Count blocks, show stats

### **Purpose**:
- **Intermediate storage** - Structured, queryable format
- **In-memory cache** - Fast access to full conversation context
- **Enrichment store** - Holds LLM-generated metadata
- **Pipeline checkpoint** - Resume from blocks without re-scraping

---

## 3️⃣ **Chroma DB** (Vector Embeddings)

### **What Gets Saved**:
- **Embeddings** - Vector representations of `flattened_text`
- **Metadata** - Searchable fields for filtering
- **Document text** - The actual `flattened_text` from block

### **Format** (ChromaDB internal format):
```python
# Each block becomes a Chroma document
{
  "id": "haval_h6_pakwheels:post_1234",  # block_id

  "embedding": [0.234, -0.891, 0.456, ...],  # 384 or 768 dimensions

  "document": """
      Post by john_doe (2025-01-15):
      What is the fuel economy of H6?

      Reply by jane_smith:
      Around 12-14 km/l in city...
  """,  # flattened_text

  "metadata": {
      "author": "john_doe",
      "start_date": "2025-01-15T10:30:00",
      "end_date": "2025-01-15T14:20:00",
      "variant": "H6 PHEV",             # From enrichment
      "sentiment": "positive",           # From enrichment
      "tags": "fuel_economy,performance", # From enrichment
      "summary": "Discussion about...",  # From enrichment
      "is_complaint": False,
      "complaint_type": None,
  }
}
```

### **Directory Structure**:
```
data/chroma_pakwheels_haval/
  ├── chroma.sqlite3           # Metadata storage
  └── {uuid}/                  # Vector index files

data/chroma_pakwheels_kia/
  ├── chroma.sqlite3
  └── {uuid}/

data/chroma_whatsapp_haval/
  ├── chroma.sqlite3
  └── {uuid}/
```

### **When Used**:
- ✅ **During queries** - Semantic search for similar conversations
- ✅ **RAG retrieval** - Find relevant context for user questions
- ✅ **Filtering** - Search by date, variant, sentiment, tags
- ❌ **NOT used for full context** - Only returns block_id, then fetches from .pkl

### **Purpose**:
- **Semantic search** - Find conversations by meaning, not just keywords
- **Fast retrieval** - Vector similarity search (milliseconds)
- **Metadata filtering** - "Show me complaints about PHEV from 2024"
- **RAG context** - Provide relevant conversations to LLM

---

## 🔄 **Complete Data Flow**

### **Pipeline Execution**:

```
┌─────────────────────────────────────────────────────┐
│ Step 1: SCRAPING                                    │
├─────────────────────────────────────────────────────┤
│ Input:  PakWheels forum URL                         │
│ Output: data/featured_research__Haval H6.json       │
│ Format: Raw JSON posts                              │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Step 2: CONVERSION TO BLOCKS                        │
├─────────────────────────────────────────────────────┤
│ Input:  featured_research__Haval H6.json            │
│ Process:                                            │
│   1. Clean HTML → plain text                        │
│   2. Group posts into conversations (root+replies)  │
│   3. Create ConversationBlock objects               │
│   4. Add block_id: haval_pakwheels:post_X           │
│ Output: In-memory blocks (not saved yet)            │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Step 3: ENRICHMENT (Optional)                       │
├─────────────────────────────────────────────────────┤
│ Input:  ConversationBlock objects                   │
│ Process:                                            │
│   1. LLM analyzes each block                        │
│   2. Extracts: variant, sentiment, tags, summary    │
│   3. Adds metadata to block objects                 │
│ Output: Enriched blocks (in-memory)                 │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Step 4: INDEXING TO CHROMA + SAVE PKL               │
├─────────────────────────────────────────────────────┤
│ Input:  Enriched blocks                             │
│ Process:                                            │
│   1. Generate embeddings from flattened_text        │
│   2. Store in Chroma with metadata                  │
│   3. Save blocks to .pkl file                       │
│ Output:                                             │
│   - data/pakwheels_blocks_haval.pkl                 │
│   - data/chroma_pakwheels_haval/                    │
└─────────────────────────────────────────────────────┘
```

### **Query Execution** (User asks a question):

```
┌─────────────────────────────────────────────────────┐
│ Step 1: USER QUERY                                  │
├─────────────────────────────────────────────────────┤
│ User: "What are common H6 PHEV problems?"           │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Step 2: SEMANTIC SEARCH (Chroma)                    │
├─────────────────────────────────────────────────────┤
│ Process:                                            │
│   1. Embed user query → vector                      │
│   2. Search Chroma for similar vectors              │
│   3. Apply filters: variant="PHEV", is_complaint    │
│ Output: List of block_ids                           │
│   ["haval_pakwheels:post_123", ...]                 │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Step 3: RETRIEVE FULL BLOCKS (PKL)                  │
├─────────────────────────────────────────────────────┤
│ Process:                                            │
│   1. Use block_ids to fetch from .pkl               │
│   2. Get full ConversationBlock objects             │
│   3. Extract flattened_text + metadata              │
│ Output: Full conversation context                   │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Step 4: LLM GENERATION                              │
├─────────────────────────────────────────────────────┤
│ Process:                                            │
│   1. Build prompt with retrieved context            │
│   2. Send to LLM (Gemini/Grok)                      │
│   3. LLM generates answer based on context          │
│ Output: AI response to user                         │
└─────────────────────────────────────────────────────┘
```

---

## 📦 **Storage Size Comparison**

### **Example (1000 posts)**:

```
JSON (Raw):
  featured_research__Haval.json:  ~5-10 MB
  - Includes HTML, avatars, metadata
  - Inefficient for searching

PKL (Blocks):
  pakwheels_blocks_haval.pkl:     ~2-5 MB
  - Cleaned text, structured data
  - Fast to load into memory
  - Includes enrichment metadata

Chroma DB (Embeddings):
  chroma_pakwheels_haval/:        ~50-100 MB
  - Vector embeddings (large!)
  - Optimized for similarity search
  - Fastest retrieval
```

---

## 🎯 **Key Differences Summary**

| Aspect | JSON | PKL | Chroma DB |
|--------|------|-----|-----------|
| **Content** | Raw posts | Conversation blocks | Embeddings + metadata |
| **Format** | Text (JSON) | Binary (pickle) | Binary (vector DB) |
| **Size** | 5-10 MB | 2-5 MB | 50-100 MB |
| **Speed** | Slow | Fast | Ultra-fast |
| **Search** | ❌ No | 🟡 Yes (load all) | ✅ Yes (indexed) |
| **Semantic** | ❌ No | ❌ No | ✅ Yes |
| **Editable** | ✅ Yes (text) | ❌ No (binary) | ❌ No (binary) |
| **Human Readable** | ✅ Yes | ❌ No | ❌ No |
| **When Created** | Scraping | Pipeline | Indexing |
| **When Used** | Pipeline input | Queries, analytics | Semantic search |
| **Can Regenerate** | ❌ No (source) | ✅ Yes (from JSON) | ✅ Yes (from PKL) |

---

## 🔁 **Dependency Chain**

```
JSON → PKL → Chroma DB
  ↑      ↑       ↑
  |      |       └─ Requires PKL blocks
  |      └───────── Requires JSON
  └──────────────── Source of truth
```

**Important**:
- ✅ Can regenerate PKL from JSON
- ✅ Can regenerate Chroma from PKL
- ❌ Cannot regenerate JSON (must rescrape)

---

## 💡 **When to Delete What**

### **Delete JSON**:
- ❌ **NEVER** - It's your source of truth
- ✅ **Only if**: You can rescrape anytime

### **Delete PKL**:
- ✅ Safe if you have JSON (can regenerate)
- ⚠️ Loses enrichment metadata (must re-enrich)

### **Delete Chroma DB**:
- ✅ Safe if you have PKL (can regenerate)
- ⚠️ Loses embeddings (must re-embed)

### **Clean Slate (Your Case)**:
```bash
# Delete everything, rescrape from scratch
rm -rf data/
mkdir data/

# Then:
# 1. Scrape → Creates JSON
# 2. Pipeline → Creates PKL
# 3. Indexing → Creates Chroma
```

---

## 📝 **Quick Reference**

**For Developers**:
- Want raw data? → JSON
- Want to query blocks? → PKL
- Want semantic search? → Chroma DB

**For Users**:
- JSON = What was scraped
- PKL = Organized conversations
- Chroma = AI search engine

---

**All three layers work together to provide fast, accurate AI responses!**
