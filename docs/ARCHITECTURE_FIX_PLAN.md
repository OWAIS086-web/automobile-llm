# Company-Source Data Separation Architecture

## 📋 Current State Analysis

### ✅ What's Working
1. **Config Structure** ([config/companies.py](config/companies.py))
   - Properly defined company-specific paths:
     - `pakwheels_blocks_file`: `data/pakwheels_blocks_{company}.pkl`
     - `whatsapp_blocks_file`: `data/whatsapp_blocks_{company}.pkl`
     - `chroma_pakwheels_path`: `data/chroma_pakwheels_{company}`
     - `chroma_whatsapp_path`: `data/chroma_whatsapp_{company}`

2. **Naming Convention** (thread_id based)
   - Haval PakWheels: `haval_h6_pakwheels:*`
   - Kia PakWheels: `kia_lucky_motors_pakwheels:*`
   - Haval WhatsApp: `whatsapp_phone_*`

### ❌ Critical Issues Found

#### **Issue #1: Block Mixing in State Restoration** 🚨
**Location**: [ai/haval_pipeline.py:248-249](ai/haval_pipeline.py#L248-L249)

```python
# PROBLEM: Adds ALL blocks to BOTH vector stores!
for b in blocks:
    pakwheels_vs.blocks_by_id[b.block_id] = b  # ❌ Wrong!
    whatsapp_vs.blocks_by_id[b.block_id] = b  # ❌ Wrong!
```

**Impact**: When pipeline restores from saved state, it adds all blocks to both PakWheels and WhatsApp vector stores, causing complete data mixing.

**Solution**: Only add blocks to their respective vector store based on block_id prefix.

---

#### **Issue #2: WhatsApp Blocks Missing Company ID** 🚨
**Location**: [ai/utils/whatsapp_data.py:225](ai/utils/whatsapp_data.py#L225)

```python
# PROBLEM: No company identifier in thread_id!
thread_id = f"{thread_prefix}_phone_{phone_number}"  # ❌ No company!
```

**Current**: `whatsapp_phone_923001234567`
**Should be**: `haval_whatsapp_phone_923001234567`

**Impact**: All companies' WhatsApp data uses same naming, causing collisions.

**Solution**: Include company_id in thread_prefix.

---

#### **Issue #3: Hardcoded mix_block.py** 🚨
**Location**: [mix_block.py:41-47](mix_block.py#L41-L47)

```python
# PROBLEM: Only works for Haval!
if block_id.startswith("haval_h6_pakwheels:"):  # ❌ Hardcoded!
    pakwheels_only[block_id] = block
elif block_id.startswith("whatsapp_"):  # ❌ No company check!
    whatsapp_only[block_id] = block
```

**Impact**: Can't separate blocks for Kia, Toyota, or future companies.

**Solution**: Make company-aware separation logic.

---

## 🎯 Robust Architecture Design

### **Principle**: Company-Source Matrix

Every piece of data should be uniquely identified by **TWO** dimensions:
1. **Company**: `haval`, `kia`, `toyota`, etc.
2. **Source**: `pakwheels`, `whatsapp`, `reddit`, `facebook`, etc.

### **Naming Convention**

#### **Block IDs**:
```
{company}_{source}:{unique_identifier}

Examples:
- haval_pakwheels:post_1234
- kia_pakwheels:post_5678
- haval_whatsapp:phone_923001234567
- toyota_reddit:thread_abc123
```

#### **File Paths**:
```
Pickle files:  data/{source}_blocks_{company}.pkl
Vector DBs:    data/chroma_{source}_{company}/
JSON files:    data/{source}_{company}_*.json

Examples:
- data/pakwheels_blocks_haval.pkl
- data/pakwheels_blocks_kia.pkl
- data/whatsapp_blocks_haval.pkl
- data/chroma_pakwheels_haval/
- data/chroma_whatsapp_haval/
```

### **Flow Diagram**

```
┌──────────────┐
│ Raw Data     │
│ Sources      │
└──────┬───────┘
       │
       ├─► PakWheels (Haval) ───┐
       ├─► PakWheels (Kia)   ───┤
       ├─► WhatsApp  (Haval) ───┤
       ├─► Reddit    (Toyota)───┤
       └─► Facebook  (Kia)   ───┤
                                │
                    ┌───────────▼────────────┐
                    │  JSON Files            │
                    │  (company_source.json) │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  Conversion Pipeline   │
                    │  ├─ Clean & Normalize  │
                    │  ├─ Create Blocks      │
                    │  └─ Add block_id with  │
                    │     {company}_{source} │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  Enrichment Pipeline   │
                    │  (OPTIONAL)            │
                    │  ├─ Variant Detection  │
                    │  ├─ Sentiment Analysis │
                    │  └─ Classification     │
                    └───────────┬────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
    ┌─────────▼─────────┐  ┌────▼───────┐  ┌─────▼──────┐
    │ Pickle Storage    │  │ Vector DB  │  │ RAG Engine │
    │ {source}_blocks_  │  │ chroma_    │  │ (per co.)  │
    │ {company}.pkl     │  │ {source}_  │  │            │
    │                   │  │ {company}/ │  │            │
    └───────────────────┘  └────────────┘  └────────────┘
          PERMANENT          SEARCHABLE      QUERYABLE
```

---

## 🔧 Implementation Plan

### **Phase 1: Fix Critical Bugs**

1. **Fix State Restoration Mixing** [haval_pipeline.py:246-250]
   ```python
   # BEFORE (❌ Wrong):
   for b in blocks:
       pakwheels_vs.blocks_by_id[b.block_id] = b
       whatsapp_vs.blocks_by_id[b.block_id] = b

   # AFTER (✅ Correct):
   for b in blocks:
       # Determine which vector store based on block_id
       if b.block_id.startswith(f"{company_id}_pakwheels:"):
           pakwheels_vs.blocks_by_id[b.block_id] = b
       elif b.block_id.startswith(f"{company_id}_whatsapp:"):
           if whatsapp_vs:
               whatsapp_vs.blocks_by_id[b.block_id] = b
   ```

2. **Add Company to WhatsApp Block IDs** [whatsapp_data.py:167]
   ```python
   def whatsapp_json_to_conversation_blocks(
       events: List[Dict[str, Any]],
       *,
       thread_prefix: str = "whatsapp",
       company_id: str = "haval",  # NEW PARAMETER
       source_url_prefix: str = "whatsapp://conversation/",
   ) -> List[ConversationBlock]:
       # ...
       thread_id = f"{company_id}_{thread_prefix}_phone_{phone_number}"
   ```

3. **Update Pipeline Calls** [haval_pipeline.py:664+]
   ```python
   elif sources == "Whatsapp":
       # ... load events ...
       blocks = whatsapp_json_to_conversation_blocks(
           events,
           thread_prefix="whatsapp",
           company_id=company_id,  # Pass company_id
       )
   ```

### **Phase 2: Make mix_block.py Company-Aware**

Create a robust separation utility that works for ALL companies:

```python
def separate_blocks_by_company_source(company_id: str):
    """
    Separate blocks for a specific company into source-specific files.

    Args:
        company_id: Company to process (e.g., 'haval', 'kia')
    """
    from config import get_company_config

    config = get_company_config(company_id)

    # Load all potential blocks
    all_blocks = {}

    # Try to load from both sources
    for source_file in [config.pakwheels_blocks_file, config.whatsapp_blocks_file]:
        if source_file and os.path.exists(source_file):
            with open(source_file, 'rb') as f:
                blocks = pickle.load(f)
                all_blocks.update(blocks)

    # Separate by source
    pakwheels_blocks = {}
    whatsapp_blocks = {}

    for block_id, block in all_blocks.items():
        if block_id.startswith(f"{company_id}_pakwheels:"):
            pakwheels_blocks[block_id] = block
        elif block_id.startswith(f"{company_id}_whatsapp:"):
            whatsapp_blocks[block_id] = block
        else:
            print(f"Warning: Unknown block type: {block_id}")

    # Save separated blocks
    # ... save logic ...
```

### **Phase 3: Add Future Source Support**

For Reddit, Facebook, or any new source:

1. **Add to config** [config/companies.py]
   ```python
   reddit_blocks_file: Optional[str] = None
   facebook_blocks_file: Optional[str] = None
   chroma_reddit_path: Optional[str] = None
   chroma_facebook_path: Optional[str] = None
   ```

2. **Create conversion function**
   ```python
   def reddit_json_to_conversation_blocks(
       posts: List[Dict],
       company_id: str,
       thread_prefix: str = "reddit"
   ):
       thread_id = f"{company_id}_{thread_prefix}:thread_{post_id}"
       # ...
   ```

3. **Add to pipeline** [haval_pipeline.py]
   ```python
   elif sources == "Reddit":
       blocks = reddit_json_to_conversation_blocks(data, company_id=company_id)
       target_vs = get_or_create_vector_store(company_id, "reddit")
   ```

---

## 🎯 Immediate Actions Needed

### **1. Clean Contaminated Haval Blocks**
```bash
# Backup current files
cp data/pakwheels_blocks.pkl data/pakwheels_blocks.pkl.contaminated_backup

# Regenerate clean Haval blocks from database (2021-2025 only)
python clean_haval_blocks.py
```

### **2. Fix the 3 Critical Bugs**
- [haval_pipeline.py:248-249] - State restoration
- [whatsapp_data.py:225] - WhatsApp thread_id
- [haval_pipeline.py:670] - Pipeline call to whatsapp converter

### **3. Update mix_block.py**
- Make it company-aware
- Support all current companies (haval, kia, toyota)

---

## ✅ Success Criteria

After implementing these fixes:

1. **Data Isolation**
   - Haval blocks contain ONLY Haval data (2021-2025)
   - Kia blocks contain ONLY Kia data (2017-2025)
   - No cross-contamination

2. **Scalability**
   - Can add Toyota, Honda, any company
   - Can add Reddit, Facebook, any source
   - No code changes to core architecture

3. **Naming Consistency**
   - All block_ids follow: `{company}_{source}:{id}`
   - All files follow: `{source}_blocks_{company}.pkl`
   - All vector DBs follow: `chroma_{source}_{company}/`

4. **AI Responses**
   - Haval users see only Haval data date ranges
   - Kia users see only Kia data date ranges
   - No wrong information due to contamination

---

## 📊 Current vs Future State

### Current (Broken)
```
pakwheels_blocks.pkl:
├─ haval_h6_pakwheels:1 (✅ Haval 2021)
├─ haval_h6_pakwheels:2 (❌ Kia 2017 - CONTAMINATED!)
├─ haval_h6_pakwheels:3 (❌ Kia 2018 - CONTAMINATED!)
└─ whatsapp_phone_923xx (✅ Haval WhatsApp)

whatsapp_blocks.pkl:
├─ whatsapp_phone_923xx (✅ Haval WhatsApp)
└─ haval_h6_pakwheels:1 (❌ MIXED!)
```

### Future (Clean)
```
pakwheels_blocks_haval.pkl:
├─ haval_pakwheels:1 (✅ Haval 2021)
├─ haval_pakwheels:2 (✅ Haval 2022)
└─ haval_pakwheels:3 (✅ Haval 2025)

pakwheels_blocks_kia.pkl:
├─ kia_pakwheels:1 (✅ Kia 2017)
├─ kia_pakwheels:2 (✅ Kia 2018)
└─ kia_pakwheels:3 (✅ Kia 2025)

whatsapp_blocks_haval.pkl:
├─ haval_whatsapp:phone_923xx (✅ Haval WhatsApp)
└─ haval_whatsapp:phone_924xx (✅ Haval WhatsApp)
```

---

**Ready to implement? I can start fixing these issues one by one.**
