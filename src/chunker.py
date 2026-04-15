import json
import tiktoken
from pathlib import Path


def count_tokens(text: str) -> int:
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except:
        return len(text.split())


def chunk_nodes(nodes: list[dict], max_tokens: int = 300) -> list[dict]:
    chunks = []
    chunk_id = 0
    
    for node in nodes:
        text = node["text"]
        token_count = count_tokens(text)
        
        if token_count <= max_tokens:
            chunks.append({
                "chunk_id": f"{node['section_id']}_chunk_{chunk_id}",
                "text": text,
                "original_id": node["section_id"],
                "parent_id": node.get("parent_id"),
                "level": node.get("level", 0),
                "references": node.get("references", []),
                "token_count": token_count
            })
            chunk_id += 1
        else:
            words = text.split()
            mid = len(words) // 2
            for i in range(0, len(words), mid):
                part = " ".join(words[i:i+mid])
                if part.strip():
                    chunks.append({
                        "chunk_id": f"{node['section_id']}_chunk_{chunk_id}",
                        "text": part,
                        "original_id": node["section_id"],
                        "parent_id": node.get("parent_id"),
                        "level": node.get("level", 0),
                        "references": node.get("references", []),
                        "token_count": count_tokens(part)
                    })
                    chunk_id += 1
    
    return chunks


def chunk_from_file(input_path: str, output_path: str = "output/chunks.json", max_tokens: int = 300):
    with open(input_path) as f:
        nodes = json.load(f)
    
    chunks = chunk_nodes(nodes, max_tokens)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(chunks, f, indent=2)
    
    print(f"Created {len(chunks)} chunks from {len(nodes)} nodes")
    return chunks


if __name__ == "__main__":
    chunks = chunk_from_file("output/nodes_with_refs.json")
    for chunk in chunks[:5]:
        print(f"  {chunk['chunk_id']}: {chunk['token_count']} tokens")