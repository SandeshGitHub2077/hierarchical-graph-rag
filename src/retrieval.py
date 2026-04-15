import json
import numpy as np
from pathlib import Path
from sentence_transformers import CrossEncoder
from neo4j import GraphDatabase


NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"


class Retriever:
    def __init__(self, index_path: str = "output/faiss/index.bin", 
                 chunks_path: str = "output/chunks.json",
                 reranker_name: str = "BAAI/bge-reranker-base"):
        import faiss
        self.index = faiss.read_index(index_path)
        with open(chunks_path) as f:
            self.chunks = json.load(f)
        self.model = CrossEncoder(reranker_name)
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    def vector_search(self, query: str, k: int = 20) -> list[dict]:
        from sentence_transformers import SentenceTransformer
        encoder = SentenceTransformer("BAAI/bge-small-en-v1.5")
        query_vec = encoder.encode([query]).astype('float32')
        distances, indices = self.index.search(query_vec, min(k, len(self.chunks)))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):
                results.append({
                    **self.chunks[idx],
                    "distance": float(dist)
                })
        return results
    
    def graph_expand(self, candidates: list[dict], max_depth: int = 2) -> list[dict]:
        seen_ids = {c["chunk_id"] for c in candidates}
        expanded = list(candidates)
        
        with self.driver.session() as session:
            for _ in range(max_depth):
                new_ids = [c["original_id"] for c in expanded if c["original_id"] not in seen_ids]
                if not new_ids:
                    break
                
                for orig_id in new_ids:
                    result = session.run("""
                        MATCH (c:Chunk {original_id: $orig_id})-[r]-(related)
                        RETURN related
                    """, orig_id=orig_id)
                    
                    for record in result:
                        related = record["related"]
                        if related and related["chunk_id"] not in seen_ids:
                            chunk = next((c for c in self.chunks if c["chunk_id"] == related["chunk_id"]), None)
                            if chunk:
                                expanded.append(chunk)
                                seen_ids.add(chunk["chunk_id"])
        
        return expanded
    
    def rerank(self, query: str, candidates: list[dict], top_n: int = 5) -> list[dict]:
        if not candidates:
            return []
        
        pairs = [(query, c["text"]) for c in candidates]
        scores = self.model.predict(pairs)
        
        for c, score in zip(candidates, scores):
            c["rerank_score"] = float(score)
        
        ranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        return ranked[:top_n]
    
    def retrieve(self, query: str, k: int = 20, top_n: int = 5) -> list[dict]:
        candidates = self.vector_search(query, k)
        expanded = self.graph_expand(candidates)
        final = self.rerank(query, expanded, top_n)
        return final
    
    def close(self):
        self.driver.close()


def retrieve(query: str) -> list[dict]:
    retriever = Retriever()
    results = retriever.retrieve(query)
    retriever.close()
    return results


if __name__ == "__main__":
    results = retrieve("What does the policy cover?")
    print(f"Retrieved {len(results)} results:")
    for r in results:
        print(f"  {r['original_id']}: {r['text'][:60]}... (score: {r.get('rerank_score', 0):.3f})")