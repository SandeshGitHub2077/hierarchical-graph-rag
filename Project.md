# Project Aim

The goal of this project is to build a **fully open-source Retrieval-Augmented Generation (RAG) system** capable of accurately understanding and answering questions from **complex, structured PDF documents**.

These documents are not simple flat text. They contain:
- Deep hierarchical structures (multi-level nesting)
- Variable numbering formats (numeric, alphabetic, roman, etc.)
- Cross-references between sections
- Uneven content distribution (some sections very large, others very small)
- Inconsistent formatting (indentation, font size, layout variations)

The system must:
- Preserve and understand document hierarchy
- Resolve cross-references correctly
- Retrieve relevant context semantically
- Filter noisy retrieval results
- Provide accurate, grounded answers using an LLM

---

# Input Data Characteristics

## 1. Hierarchical Structure

Documents follow deeply nested patterns such as:

```text
1.
  a.
    i.
      a.
```

This hierarchy can extend multiple levels and must be preserved.

---

## 2. Variable Numbering Styles

The structure is consistent within a single PDF but may vary across documents:
- Numeric (1, 2, 3)
- Alphabetic (a, b, c)
- Roman (i, ii, iii)
- Mixed combinations

---

## 3. Cross-References

Sections may reference other sections:

```text
refer to 2.a
refer to 1.a.i.a
```

These references create **non-linear relationships**, forming a graph structure.

---

## 4. Uneven Content Distribution

Examples:
- Some sections contain 1 sentence
- Some sections contain 200–500 sentences

This requires selective chunking.

---

## 5. Inconsistent Formatting

As seen in the provided image:
- Indentation varies
- Font sizes differ
- Layout is not strictly uniform

Hierarchy must be inferred using:
- Position (x-coordinates)
- Spacing (y-gaps)
- Numbering patterns

---

# System Requirements

The system must:
1. Parse PDFs into structured representations
2. Build a hierarchical tree of sections
3. Extract and link cross-references
4. Handle large and small text segments intelligently
5. Support semantic retrieval
6. Expand context using structural and reference relationships
7. Filter retrieved content using reranking
8. Generate accurate answers using a local LLM

---

# Final Architecture Overview

This is a **Hybrid RAG system combining Tree + Graph + Vector retrieval with reranking**.

---

# 1. PDF Parsing

**Tool:**
- PyMuPDF (fitz)

**Purpose:**
- Extract text blocks
- Capture coordinates (x, y)
- Capture font metadata

**Key Output:**
- Text segments with positional data for hierarchy inference

---

# 2. Structure Builder (Hierarchy / Tree)

**Tools:**
- Python + Regex (core)
- Optional: anytree

**Purpose:**
- Construct hierarchical structure:
  ```text
  1 → a → i → a
  ```

**Signals Used:**
- Numbering patterns
- Indentation (x-coordinate)
- Vertical spacing

---

# 3. Reference Extraction (Graph Edges)

**Tools:**
- Regex
- Optional: spaCy (only if references become natural language)

**Purpose:**
- Detect references such as:
  ```text
  refer to 2.a
  refer to 1.a.i.a
  ```
- Convert into graph edges

---

# 4. Custom Chunking

**Tool:**
- Custom Python implementation

**Strategy:**
- Only split large nodes (>300 tokens)
- Keep small nodes intact
- Preserve hierarchy and identity

**Example:**
```json
{
  "id": "2.a.chunk_1",
  "parent": "2.a",
  "original_id": "2.a"
}
```

---

# 5. Embeddings

**Tool:**
- sentence-transformers

**Model:**
- bge-small-en (primary choice)

**Alternative:**
- nomic-embed-text (available via Ollama)

**Purpose:**
- Convert nodes into vector representations for semantic search

---

# 6. Vector Database

**Tool:**
- FAISS

**Purpose:**
- Fast local similarity search
- Stores embeddings of all nodes/chunks

---

# 7. Graph Database

**Tool:**
- Neo4j Desktop

**Purpose:**
- Store relationships:
  - Parent-child hierarchy
  - Cross-references

**Edge Types:**
- `PARENT_OF`
- `REFERENCES`

---

# 8. Retrieval Layer

**Tool:**
- LlamaIndex

**Purpose:**
- Coordinate retrieval from:
  - Vector DB (semantic)
  - Graph DB (structural expansion)

---

# 9. Reranking Layer

**Tool:**
- bge-reranker-base (CrossEncoder)

**Purpose:**
- Improve precision after retrieval
- Filter irrelevant or weakly relevant chunks

---

## Reranking Process

1. Retrieve top-K candidates from FAISS  
2. Expand candidates via graph traversal  
3. Score each (query, chunk) pair  
4. Select top N (e.g., 5–8 chunks)  

**Example:**
```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('BAAI/bge-reranker-base')

scores = reranker.predict([
    (query, chunk_text) for chunk_text in candidates
])
```

---

# 10. LLM Layer

**Primary Model:**
- qwen3.5:9b (via Ollama)

**Alternatives:**
- llama3.1:8b
- llama3.2:3b (lighter, less capable)

**Purpose:**
- Generate final answers using structured context

---

# Full Retrieval Flow

```text
User Query
   ↓
Query Embedding
   ↓
FAISS Search (Top-K nodes)
   ↓
Graph Expansion (Neo4j)
   ↓
Candidate Pool (20–40 chunks)
   ↓
Reranking (bge-reranker)
   ↓
Top Context (5–8 chunks)
   ↓
LLM (Qwen via Ollama)
   ↓
Final Answer
```

---

# Context Construction Strategy

Before passing to the LLM, structure the context:

```text
[Main Section: 2.b.i.a]
...

[Referenced Section: 1.a.i.a]
...

[Parent Section: 2.b]
...
```

This improves reasoning and reduces hallucination.

---

# Final Stack Summary

| Layer | Tool |
|------|------|
| PDF Parsing | PyMuPDF |
| Structure | Regex + Custom Parser |
| References | Regex |
| Chunking | Custom Python |
| Embeddings | sentence-transformers (bge-small-en) |
| Vector DB | FAISS |
| Graph DB | Neo4j Desktop |
| Retrieval | LlamaIndex |
| Reranking | bge-reranker-base |
| LLM | qwen3.5:9b (Ollama) |

---

# Key Insight

The most critical component in this system is not the LLM or embeddings, but:
- Accurate structure extraction
- Correct reference linking

If those are implemented correctly, the rest of the system will perform at a very high level.
