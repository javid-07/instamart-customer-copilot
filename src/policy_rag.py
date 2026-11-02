
from pathlib import Path


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
