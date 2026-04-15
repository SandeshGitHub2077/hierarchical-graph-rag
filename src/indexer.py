import json
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase


NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"


class Indexer:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    def create_embeddings(self, texts: list[str]) -> np.ndarray:
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings
    
    def build_faiss_index(self, embeddings: np.ndarray, output_path: str = "output/faiss/index.bin"):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        index = faiss.IndexFlatL2(self.dimension)
        index.add(embeddings.astype('float32'))
        faiss.write_index(index, output_path)
        print(f"FAISS index saved to {output_path}")
        return index
    
    def load_faiss_index(self, input_path: str = "output/faiss/index.bin"):
        return faiss.read_index(input_path)
    
    def build_neo4j_graph(self, chunks: list[dict]):
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            
            for chunk in chunks:
                session.run("""
                    CREATE (c:Chunk {
                        chunk_id: $chunk_id,
                        text: $text,
                        original_id: $original_id,
                        parent_id: $parent_id,
                        level: $level,
                        references: $references
                    })
                """, chunk_id=chunk["chunk_id"], text=chunk["text"],
                   original_id=chunk["original_id"],
                   parent_id=chunk.get("parent_id"),
                   level=chunk.get("level", 0),
                   references=chunk.get("references", []))
            
            for chunk in chunks:
                parent_id = chunk.get("parent_id")
                if parent_id:
                    session.run("""
                        MATCH (c:Chunk {original_id: $original_id})
                        MATCH (p:Chunk {original_id: $parent_id})
                        CREATE (p)-[:PARENT_OF]->(c)
                    """, original_id=chunk["original_id"], parent_id=parent_id)
                
                for ref in chunk.get("references", []):
                    session.run("""
                        MATCH (c:Chunk {original_id: $original_id})
                        MATCH (r:Chunk {original_id: $ref_id})
                        CREATE (c)-[:REFERENCES]->(r)
                    """, original_id=chunk["original_id"], ref_id=ref)
        
        driver.close()
        print(f"Neo4j graph built with {len(chunks)} nodes")


def index_chunks(chunks_path: str = "output/chunks.json"):
    indexer = Indexer()
    
    with open(chunks_path) as f:
        chunks = json.load(f)
    
    texts = [c["text"] for c in chunks]
    embeddings = indexer.create_embeddings(texts)
    
    indexer.build_faiss_index(embeddings)
    indexer.build_neo4j_graph(chunks)
    
    return embeddings, chunks


def load_indexer():
    return Indexer()


if __name__ == "__main__":
    embeddings, chunks = index_chunks()
    print(f"Indexed {len(chunks)} chunks with {embeddings.shape[1]}D embeddings")