import re
import json
from pathlib import Path


NUMBERING_PATTERNS = [
    r"^(\d+)\.",           # 1.
    r"^([a-z])\.",         # a.
    r"^([a-z])\.",         # a (lowercase)
    r"^([A-Z])\.",        # A (uppercase)
    r"^([i]+)\.$",         # i.
    r"^([ivxlcdm]+)\.$",    # ivxlcdm roman
    r"^([I]+)\.$",         # I.
    r"^([IVXLCDM]+)\.$",    # IVXLCDM roman
    r"^\((\d+)\)",        # (1)
    r"^\((\d+)\)",        # (a)
]


def detect_numbering(text: str) -> tuple[str, str] | None:
    for pattern in NUMBERING_PATTERNS:
        match = re.match(pattern, text.strip())
        if match:
            return (match.group(1), pattern)
    return None


def get_level(numbering: str, pattern: str) -> int:
    if re.match(r"^(\d+)\.", pattern) or re.match(r"^\((\d+)\)", pattern):
        return 0
    if re.match(r"^([a-z])\.", pattern) or re.match(r"^\(([a-z])\)", pattern):
        return 1
    if re.match(r"^([i]+)\.$", pattern) or re.match(r"^([ivxlcdm]+)\.$", pattern):
        return 2
    if re.match(r"^([A-Z])\.", pattern):
        return 1
    if re.match(r"^([I]+)\.$", pattern) or re.match(r"^([IVXLCDM]+)\.$", pattern):
        return 0
    return 0


def infer_section_id(numbering: str, parent_id: str | None) -> str:
    if parent_id:
        return f"{parent_id}.{numbering}"
    return numbering


def build_hierarchy(blocks: list[dict]) -> list[dict]:
    nodes = []
    stack = []
    
    for block in blocks:
        text = block["text"]
        result = detect_numbering(text)
        
        if result:
            numbering, pattern = result
            level = get_level(numbering, pattern)
            
            while stack and stack[-1]["level"] >= level:
                stack.pop()
            
            parent_id = stack[-1]["section_id"] if stack else None
            section_id = infer_section_id(numbering, parent_id)
            
            node = {
                "text": text,
                "section_id": section_id,
                "level": level,
                "parent_id": parent_id,
                "x0": block["x0"],
                "y0": block["y0"],
                "page": block["page"]
            }
            nodes.append(node)
            stack.append(node)
        else:
            if nodes:
                nodes[-1]["text"] += " " + text
    
    return nodes


def build_from_file(input_path: str, output_path: str = "output/nodes_hierarchical.json"):
    with open(input_path) as f:
        blocks = json.load(f)
    
    nodes = build_hierarchy(blocks)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(nodes, f, indent=2)
    
    print(f"Built {len(nodes)} hierarchical nodes to {output_path}")
    return nodes


if __name__ == "__main__":
    nodes = build_from_file("output/nodes.json")
    for node in nodes[:5]:
        print(f"  {node['section_id']}: {node['text'][:50]}...")