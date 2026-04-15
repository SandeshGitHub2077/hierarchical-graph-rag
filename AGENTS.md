# AGENTS.md

## Secrets

All secrets (Neo4j password, etc.) must go in `.env` file. Create one if missing:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

## Prerequisites

- Neo4j Desktop running on localhost:7687
- Ollama running with models: `qwen3.5:9b`, `llama3.2:3b`, `llama3.1:8b`

## Commands

```bash
# Run all tests
pytest tests/ -v

# Index a PDF
python -m src.parser data/pdfs/yourfile.pdf

# Query the system
python -m src.llm "your question here"

# Run retrieval directly
python -m src.retrieval "your question here"
```

## Architecture

- **Hybrid RAG**: Vector (FAISS) → Graph (Neo4j parent-child + cross-refs) → Rerank → LLM
- **Pipeline**: parser → builder → extractor → chunker → indexer → retrieval → llm
- **Key files**:
  - `src/parser.py` - PDF extraction (PyMuPDF)
  - `src/builder.py` - Hierarchy from x/y coords + numbering patterns
  - `src/extractor.py` - Regex cross-reference extraction ("refer to X.Y.Z")
  - `src/chunker.py` - Split nodes >300 tokens, keep small intact
  - `src/indexer.py` - FAISS + Neo4j indexing
  - `src/retrieval.py` - Vector search → graph expand → rerank (bge-reranker-base)
  - `src/llm.py` - Ollama query (fallback: llama3.2:3b → llama3.1:8b → qwen3.5:9b)