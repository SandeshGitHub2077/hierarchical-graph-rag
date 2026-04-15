import json
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2:3b"
FALLBACK_MODELS = ["llama3.1:8b", "qwen3.5:9b"]


def build_context(chunks: list[dict]) -> str:
    context_parts = []
    for chunk in chunks:
        header = f"[Section: {chunk.get('original_id', chunk.get('chunk_id', 'unknown'))}]"
        context_parts.append(f"{header}\n{chunk['text']}")
    return "\n\n".join(context_parts)


def query_ollama(prompt: str, model: str = DEFAULT_MODEL, timeout: int = 300) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()["response"]
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
        if model != DEFAULT_MODEL:
            raise
        for fallback in FALLBACK_MODELS:
            try:
                print(f"Primary model timed out, trying fallback: {fallback}")
                return query_ollama(prompt, model=fallback, timeout=timeout)
            except Exception:
                continue
        raise


def ask(query: str, context_chunks: list[dict]) -> str:
    context = build_context(context_chunks)
    full_prompt = f"""You are a helpful assistant. Use the provided context to answer the question accurately.

Context:
{context}

Question: {query}

Answer:"""
    return query_ollama(full_prompt)


if __name__ == "__main__":
    from src.retrieval import retrieve
    chunks = retrieve("What does the policy cover?")
    answer = ask("What does the policy cover?", chunks)
    print(f"Q: What does the policy cover?")
    print(f"A: {answer}")