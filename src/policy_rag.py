from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "data" / "policies"

def chunk_documents(chunk_size=40, overlap=10):
    """Split policy documents into overlapping word chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between 0 and chunk_size")

    chunks = []
    step = chunk_size - overlap

    for file_path in sorted(POLICY_DIR.glob("*.txt")):
        text = file_path.read_text(encoding="utf-8")
        words = text.split()

        for start in range(0, len(words), step):
            end = start + chunk_size

            chunk_text = " ".join(words[start:end])

            chunks.append({
                "source": file_path.name,
                "text": chunk_text,
            })

            if end >= len(words):
                break

    return chunks

# Fitting TF-IDF on all policy chunks.
CHUNKS = chunk_documents()
CHUNK_TEXTS = [chunk["text"] for chunk in CHUNKS]

VECTORIZER = TfidfVectorizer()
TFIDF_MATRIX = VECTORIZER.fit_transform(CHUNK_TEXTS)

def retrieve(query, k=3):
    """Retrieving the top-k policy chunks using cosine similarity."""

    query_vector = VECTORIZER.transform([query])

    similarities = cosine_similarity(
        query_vector,
        TFIDF_MATRIX,
    ).flatten()

    top_indices = similarities.argsort()[::-1][:k]

    results = []

    for index in top_indices:
        results.append({
            "source": CHUNKS[index]["source"],
            "score": float(similarities[index]),
            "text": CHUNKS[index]["text"],
        })

    return results


if __name__ == "__main__":
    chunks = chunk_documents()

    print("Total chunks:", len(chunks))

    for source in sorted({chunk["source"] for chunk in chunks}):
        count = sum(
            chunk["source"] == source for chunk in chunks
        )
        print(f"{source}: {count}")

    assert len(chunks) == 15, "Expected exactly 15 chunks"

    expected_counts = {
        "refund_policy.txt": 4,
        "delivery_policy.txt": 3,
        "escalation_policy.txt": 3,
        "payment_policy.txt": 3,
        "privacy_policy.txt": 2,
    }

    actual_counts = {
        source: sum(chunk["source"] == source for chunk in chunks)
        for source in expected_counts
    }

    assert actual_counts == expected_counts

    print("Chunk validation: PASS")
