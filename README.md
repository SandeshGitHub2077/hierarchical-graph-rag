# Hierarchical Graph RAG

Hybrid RAG system combining vector search (FAISS), knowledge graph (Neo4j), and reranking for PDF document question answering.

## Quick Start

```bash
# Run tests
pytest tests/ -v

# Index a PDF
python -m src.parser data/pdfs/yourfile.pdf

# Query
python -m src.llm "your question here"
```

## Architecture

```
PDF → Parser → Builder → Extractor → Chunker → Indexer → Retrieval → LLM
                                    ↓                          ↓
                              (FAISS + Neo4j)            (Ollama)
```

- **Vector Search**: FAISS with BAAI/bge-small-en-v1.5
- **Graph**: Neo4j for parent-child hierarchy + cross-references
- **Reranking**: BAAI/bge-reranker-base
- **LLM**: Ollama (qwen3.5:9b, llama3.1:8b, llama3.2:3b fallback)

## Prerequisites

- Neo4j Desktop on localhost:7687
- Ollama with models: `qwen3.5:9b`, `llama3.2:3b`, `llama3.1:8b`
- Copy `.env.example` to `.env` with Neo4j credentials

## Project Structure

```
src/
├── parser.py      # PDF extraction (PyMuPDF)
├── builder.py     # Hierarchy from x/y coords
├── extractor.py   # Cross-reference detection
├── chunker.py    # Token-based chunking
├── indexer.py    # FAISS + Neo4j indexing
├── retrieval.py  # Vector → Graph → Rerank
└── llm.py        # Ollama integration
```
