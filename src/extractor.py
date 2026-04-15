import re
import json
from pathlib import Path


REFERENCE_PATTERNS = [
    r"(?:refer to|see|referenced in|as stated in|as detailed in|outlined in|described in)\s+([\d\.\s]+[a-z](?:\.[a-z])*)",
    r"(?:section|\S?\s?)\s*([\d]+(?:\.[a-z])+(?:\.[a-z])*)",
]


def extract_references(text: str) -> list[str]:
    references = []
    text_lower = text.lower()
    
    for pattern in REFERENCE_PATTERNS:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            cleaned = re.sub(r'\s+', '.', match.strip().strip('.'))
            cleaned = re.sub(r'^\.', '', cleaned)
            if cleaned and re.match(r'^[\d]+', cleaned):
                references.append(cleaned)
    
    return list(set(references))


def add_references(nodes: list[dict]) -> list[dict]:
    for node in nodes:
        node["references"] = extract_references(node["text"])
    return nodes


def add_references_from_file(input_path: str, output_path: str):
    with open(input_path) as f:
        nodes = json.load(f)
    
    nodes = add_references(nodes)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(nodes, f, indent=2)
    
    ref_count = sum(1 for n in nodes if n.get("references"))
    print(f"Added references to {len(nodes)} nodes, {ref_count} have references")
    return nodes


if __name__ == "__main__":
    nodes = add_references_from_file("output/nodes_hierarchical.json", "output/nodes_with_refs.json")
    for node in nodes[:5]:
        if node.get("references"):
            print(f"  {node['section_id']}: {node['references']}")