import pytest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser import extract_pdf, extract_to_file
from src.builder import build_hierarchy, detect_numbering, get_level
from src.extractor import extract_references, add_references
from src.chunker import chunk_nodes, count_tokens


class TestParser:
    def test_extract_pdf(self):
        blocks = extract_pdf("data/pdfs/ddh.pdf")
        assert len(blocks) > 0
        assert "text" in blocks[0]
        assert "x0" in blocks[0]
        assert "y0" in blocks[0]
    
    def test_extract_synthetic(self):
        blocks = extract_pdf("data/pdfs/synthetic.pdf")
        assert len(blocks) > 0


class TestBuilder:
    def test_detect_numbering_numeric(self):
        result = detect_numbering("1. Introduction")
        assert result is not None
        assert result[0] == "1"
    
    def test_detect_numbering_alpha(self):
        result = detect_numbering("a. First item")
        assert result is not None
    
    def test_detect_numbering_roman(self):
        result = detect_numbering("i. First")
        assert result is not None
    
    def test_build_hierarchy(self):
        blocks = [
            {"text": "1. Section", "x0": 72, "y0": 60, "page": 1},
            {"text": "a. Subsection", "x0": 90, "y0": 80, "page": 1},
            {"text": "Content here", "x0": 72, "y0": 100, "page": 1},
        ]
        nodes = build_hierarchy(blocks)
        assert len(nodes) >= 1


class TestExtractor:
    def test_extract_references_simple(self):
        refs = extract_references("refer to 2.a")
        assert "2.a" in refs
    
    def test_extract_references_section(self):
        refs = extract_references("See section 1.a.i for details")
        assert len(refs) >= 1
    
    def test_extract_references_multiple(self):
        refs = extract_references("refer to 2.a and 1.b.iii")
        assert len(refs) == 2
    
    def test_add_references(self):
        nodes = [{"text": "refer to 1.a", "section_id": "2.a", "level": 0}]
        result = add_references(nodes)
        assert "references" in result[0]
        assert "1.a" in result[0]["references"]


class TestChunker:
    def test_count_tokens(self):
        tokens = count_tokens("This is a test sentence")
        assert tokens > 0
    
    def test_chunk_nodes_small(self):
        nodes = [
            {"text": "Short text", "section_id": "1", "level": 0, "parent_id": None, "references": []}
        ]
        chunks = chunk_nodes(nodes, max_tokens=300)
        assert len(chunks) == 1
    
    def test_chunk_nodes_large(self):
        text = " ".join(["word"] * 500)
        nodes = [
            {"text": text, "section_id": "1", "level": 0, "parent_id": None, "references": []}
        ]
        chunks = chunk_nodes(nodes, max_tokens=300)
        assert len(chunks) > 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])