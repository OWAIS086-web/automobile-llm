# 🏪 Dealership Database Test Prompts

**For Director Demo - Ready to Use**

## ✅ Prerequisites
1. Seed the database: `python seed_dealership_data.py`
2. Start server and login
3. Select **Dealership Data** mode from dropdown

---

## 📊 **AGGREGATION QUERIES** (Count, Sum, Statistics)

### Basic Counts
```
How many tyre complaints in December?
```
```
Total warranty claims in the database?
```
```
Total warranty claims in the database?Total warranty claims in the database?
```

### Group By Queries
```
Which dealership has the most warranty claims?
```
```
Show me PDI inspections by dealership
```
```
Which car model has most complaints - H6 or Jolion?
```
```
How many campaigns did each dealership complete?
```

### Date Range Queries
```
Show warranty claims from last month
```
```
PDI inspections in 2024
```
```
How many FFS inspections between January and March?
```

---

## 🔍 **FILTERING QUERIES** (Specific Records)

### By VIN Number
```
Show warranty claims for VIN [use any VIN from seed data]
```
```
Show all service records for VIN number [VIN]
```

### By Dealership
```
Show warranty claims for Lahore dealership
```
```
PDI inspections at Haval Central
```
```
All repair orders from Karachi dealership
```

### By Claim Type
```
Show all engine complaints
```
```
Filter tyre warranty claims
```
```
Show electrical issues only
```

---

## 📈 **COMPARISON QUERIES** (Compare Entities)

### Dealership Comparison
```
Compare Lahore vs Karachi warranty claims
```
```
Which has more PDI inspections - Islamabad or Rawalpindi?
```
```
Lahore vs Karachi campaign completions
```

### Model Comparison
```
H6 vs Jolion warranty claims
```
```
Compare complaint rates between Haval H6 and Jolion
```
```
Which model has more service issues - H6 PHEV or regular H6?
```

---

## 🔄 **HISTORY QUERIES** (Complete VIN Timeline)

```
Show complete history for VIN [VIN from database]
```
```





















```
```
Show all service records for VIN [VIN]
```
```
Give me the service timeline for VIN [VIN]
```

---

## 🔎 **SEMANTIC QUERIES** (Text Search)

```
Show complaints about brake noise
```
```
Find warranty claims mentioning transmission issues
```
```
Which cars had engine problems?
```
```
Search for electrical complaints
```

---

## 💡 **ADVANCED QUERIES** (Multi-Criteria)

### Complex Filters
```
Show tyre complaints from Lahore dealership in December
```
```
H6 warranty claims in the last 6 months
```
```
PDI inspections with objections at Karachi dealership
```

### Top N Queries
```
Top 10 VINs with most complaints
```
```
Which 5 dealerships have highest PDI objection rates?
```
```
Show top 3 most complained car models
```

### Ratio/Percentage Questions
```
What percentage of PDI inspections had objections?
```
```
Ratio of approved vs rejected warranty claims
```
```
PDI pass rate by dealership
```

---

## 🔄 **FOLLOW-UP QUESTIONS** (Tests Context Handling)

### Example Conversation 1:
```
Q1: How many tyre complaints in December?
Q2: What about November?          ← Follow-up (should inherit "tyre complaints")
Q3: And for Lahore dealership?    ← Follow-up (should add dealership filter)
```

### Example Conversation 2:
```
Q1: Which dealership has most PDI inspections?
Q2: What about campaigns?          ← Follow-up (switches to campaigns, keeps dealership context)
Q3: Show the breakdown              ← Follow-up (asks for details)
```

### Example Conversation 3:
```
Q1: Compare H6 vs Jolion warranty claims
Q2: What about Lahore dealership?  ← Follow-up (adds dealership filter to comparison)
Q3: Show by month                   ← Follow-up (adds time breakdown)
```

---

## 🎯 **TYPO TOLERANCE TESTS** (LLM Entity Extraction)

### Spelling Mistakes
```
How many tire complaints?          (tire → tyre)
```
```
Havl H6 warrenty claims           (Haval, warranty typos)
```
```
Julion vs H 6 complaints          (Jolion, spacing)
```

### Abbreviations
```
lhr vs khi PDI inspections        (Lahore vs Karachi)
```
```
isb dealership complaints         (Islamabad)
```
```
Show ROs for rwp                  (Repair Orders, Rawalpindi)
```

---

## 🚀 **DEMO FLOW SUGGESTIONS**

### **Flow 1: Overview & Counts** (2 minutes)
1. "How many warranty claims in total?"
2. "Which dealership has the most?"
3. "Show me the breakdown by claim type"

### **Flow 2: Specific Investigation** (3 minutes)
1. "Show warranty claims for Lahore dealership"
2. "Which VIN has most complaints?"
3. "Show complete history for that VIN"

### **Flow 3: Comparison Analysis** (3 minutes)
1. "Compare H6 vs Jolion warranty claims"
2. "Which dealership handles H6 better?"
3. "Show me PDI objection rates by dealership"

### **Flow 4: Follow-Up Intelligence** (2 minutes)
1. "How many tyre complaints in December?"
2. "What about November?"
3. "And which dealership had most?"

---

## ⚠️ **EDGE CASES TO TEST**

### Empty Results
```
Show warranty claims for VIN DOESNOTEXIST12345
```
Expected: Helpful "no results" message with suggestions

### Invalid Queries
```
Delete all warranty claims        ← Should be blocked by SQL validation
```
Expected: Safety message

### Ambiguous Queries
```
Show me data                      ← Too vague
```
Expected: Request for clarification

---

## 📋 **QUICK COPY-PASTE LIST** (For Fast Testing)

```
How many tyre complaints in December?
Which dealership has most warranty claims?
Show warranty claims for Lahore dealership
Compare H6 vs Jolion complaints
Top 10 VINs with most complaints
Show PDI inspections with objections
How many campaigns did Karachi complete?
What percentage of PDIs had objections?
Show complaints about brake noise
[Pick a VIN from database] Show complete history for VIN ABCD...
```

---

## 🎬 **DIRECTOR DEMO SCRIPT** (Recommended)

### **Opening** (30 seconds)
"I'll demonstrate our LLM-powered natural language interface for the dealership database. Unlike traditional SQL dashboards, you can ask questions in plain English."

### **Demo** (3-4 minutes)

**1. Basic Query:**
```
"How many warranty claims in total?"
```
*Show it answers: "X warranty claims"*

**2. Aggregation:**
```
"Which dealership has the most?"
```
*Show breakdown table*

**3. Comparison:**
```
"Compare H6 vs Jolion warranty claims"
```
*Show comparison with insights*

**4. Follow-Up:**
```
"What about just Lahore dealership?"
```
*Show context awareness*

**5. VIN History:**
```
"Show complete history for VIN [pick one]"
```
*Show comprehensive timeline*

### **Closing** (30 seconds)
"The system handles typos, abbreviations, and follow-up questions automatically. It's production-ready with SQL injection protection and works with your existing dealership database."

---

## ✅ **SUCCESS CRITERIA**

- ✅ All basic counts work
- ✅ GROUP BY queries return formatted tables
- ✅ Comparisons show insights
- ✅ Follow-ups inherit context
- ✅ VIN history shows complete timeline
- ✅ Typos are handled gracefully
- ✅ Invalid SQL is blocked
- ✅ Empty results give helpful messages

---

## 🔧 **TROUBLESHOOTING**

### If query fails:
1. Check logs for SQL generation issues
2. Try simpler version of question
3. Verify database has been seeded

### If no results:
- Database might be empty → Run `python seed_dealership_data.py`
- Check VIN numbers in database → Use actual VINs from seed data

### If mode not available:
- Refresh page
- Check you're logged in as Haval user
- Verify `Dealership Data` button appears in mode dropdown

---

**Good luck with your demo In sha Allah! 🚀**
