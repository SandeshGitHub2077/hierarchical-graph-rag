# Implementation Plan

## Directory Structure

```
alliance_rag/
├── src/
│   ├── __init__.py
│   ├── parser.py          # PDF parsing with PyMuPDF
│   ├── builder.py        # Structure/hierarchy builder
│   ├── extractor.py      # Reference extractor
│   ├── chunker.py       # Custom chunking
│   ├── indexer.py      # FAISS + Neo4j indexing
│   ├── retrieval.py      # Retrieval (vector + graph + rerank)
│   ├── llm.py           # Ollama integration
│   └── api.py           # End-to-end query API
├── data/
│   └── pdfs/            # Input PDFs (placeholder)
├── output/
│   ├── nodes.json       # Parsed nodes
│   ├── chunks.json      # Chunked nodes
│   ├── faiss/           # FAISS index files
│   └── graph/            # Graph export (optional)
├── tests/
│   ├── test_parser.py
│   ├── test_builder.py
│   ├── test_extractor.py
│   └── test_chunker.py
├── TASKFILE.md
├── AGENTS.md
└── requirements.txt
```

## Implementation Details

### Phase 1: Core Infrastructure (1.1 - 1.4)

| Step | File | Functionality | Output |
|------|------|---------------|--------|
| 1.1 | `src/parser.py` | `extract_pdf(path)` → blocks with text, x, y, font | `output/nodes.json` |
| 1.2 | `src/builder.py` | `build_hierarchy(blocks)` → tree with section IDs | Adds `section_id`, `level` to nodes |
| 1.3 | `src/extractor.py` | `extract_references(text)` → list of `["2.a", "1.b.iii"]` | Adds `references` to nodes |
| 1.4 | `src/chunker.py` | `chunk_nodes(nodes, max_tokens=300)` → chunks | `output/chunks.json` |

### Phase 2: Data Pipeline (2.1 - 2.3)

| Step | File | Functionality | Output |
|------|------|---------------|--------|
| 2.1 | `src/indexer.py` | `create_embeddings(chunks)` → vectors | In-memory, exportable |
| 2.2 | `src/indexer.py` | `build_faiss_index(vectors)` → FAISS index | `output/faiss/` |
| 2.3 | `src/indexer.py` | `build_neo4j_graph(nodes, chunks)` → edges | Neo4j DB |

### Phase 3: Retrieval System (3.1 - 3.3)

| Step | File | Functionality |
|------|------|---------------|
| 3.1 | `src/retrieval.py` | `vector_search(query, k=20)` → top-K candidates |
| 3.2 | `src/retrieval.py` | `graph_expand(candidates)` → expand with parent-child + refs |
| 3.3 | `src/retrieval.py` | `rerank(query, candidates, top_n=5)` → final chunks |

### Phase 4: LLM Integration (4.1 - 4.3)

| Step | File | Functionality |
|------|------|---------------|
| 4.1 | `src/llm.py` | `build_context(chunks)` → formatted prompt |
| 4.2 | `src/llm.py` | `query_ollama(prompt, model="qwen3.5:9b")` → response |
| 4.3 | `src/api.py` | `query(query_text)` → final answer |

## Synthetic Test Data

Create a PDF with:
- 3-4 sections with nested hierarchy (1, 1.a, 1.a.i, 1.a.ii)
- Mixed numbering (numeric, alphabetic, roman)
- Cross-references between sections
- Varying content length (1 sentence to ~20 sentences per section)

## Neo4j Schema

```
Node: Chunk
  - id: string (e.g., "2.a.iii")
  - original_id: string
  - text: string
  - level: int
  - parent_id: string (nullable)
  - references: list[string]

Edge: PARENT_OF (from parent to child)
Edge: REFERENCES (from section to referenced section)
```

## Verification

After each step, verify output and update TASKFILE.md with status.

## Run Commands

```bash
# Activate venv
source .venv/bin/activate

# Run parser
python -m src.parser data/pdfs/input.pdf

# Run full pipeline
python -m src.api "Your question here"
```