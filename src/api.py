from src.retrieval import retrieve
from src.llm import ask


def query(query_text: str, debug: bool = False) -> str:
    chunks = retrieve(query_text)
    answer = ask(query_text, chunks)
    if debug:
        return {
            "query": query_text,
            "retrieved_chunks": chunks,
            "answer": answer
        }
    return answer


if __name__ == "__main__":
    import sys
    query_text = sys.argv[1] if len(sys.argv) > 1 else "What does the policy cover?"
    result = query(query_text, debug=True)
    print(f"Q: {result['query']}")
    print(f"\nRetrieved {len(result['retrieved_chunks'])} chunks:")
    for chunk in result['retrieved_chunks']:
        print(f"  - {chunk['original_id']}")
    print(f"\nA: {result['answer']}")