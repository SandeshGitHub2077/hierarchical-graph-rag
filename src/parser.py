import fitz
import json
from pathlib import Path


def extract_pdf(pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    blocks = []
    
    for page_num, page in enumerate(doc):
        text_dict = page.get_text("dict")
        for block in text_dict["blocks"]:
            if block["type"] == 0:
                for line in block["lines"]:
                    text = ""
                    for span in line["spans"]:
                        text += span["text"]
                    if text.strip():
                        blocks.append({
                            "text": text.strip(),
                            "x0": line["bbox"][0],
                            "y0": line["bbox"][1],
                            "x1": line["bbox"][2],
                            "y1": line["bbox"][3],
                            "page": page_num + 1
                        })
    
    doc.close()
    return blocks


def extract_to_file(pdf_path: str, output_path: str = "output/nodes.json"):
    blocks = extract_pdf(pdf_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(blocks, f, indent=2)
    print(f"Extracted {len(blocks)} blocks to {output_path}")
    return blocks


if __name__ == "__main__":
    import sys
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "data/pdfs/synthetic.pdf"
    blocks = extract_to_file(pdf_path)
    print(f"First block: {blocks[0]}")