import sys
from pathlib import Path
import re
import pandas as pd
import random
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import mock_llm

TICKETS_PATH = ROOT / "data" / "raw" / "tickets.csv"
MAX_INPUT_TOKENS = 400
BASE_DELAY = 0.05
MAX_RETRIES = 3

def call_with_retries(ticket_id, messages):
    """Calling the mock LLM with exponential backoff and jitter."""

    for retry_number in range(MAX_RETRIES + 1):
        try:
            return mock_llm.chat(messages)

        except mock_llm.TransientLLMError:
            if retry_number == MAX_RETRIES:
                raise

            wait = (
                BASE_DELAY
                * (2 ** retry_number)
                * random.uniform(0.9, 1.15)
            )

            print(
                f"Retry: ticket_id={ticket_id}, "
                f"retry_number={retry_number}, "
                f"wait={wait:.4f}s"
            )

            time.sleep(wait)

ZERO_SHOT_PROMPT = """
CLASSIFY the customer support ticket into exactly one of these categories:
billing, delivery, technical, fraud.

Return a JSON-only reply in this exact form:
{"category": "...", "reason": "..."}

Do not include markdown, code fences, or any text outside the JSON object.
The category must be one of the four allowed categories.
The reason must briefly explain the classification.
""".strip()

FEW_SHOT_PROMPT = """
CLASSIFY the customer support ticket into exactly one of these categories:
billing, delivery, technical, fraud.

Return a JSON-only reply in this exact form:
{"category": "...", "reason": "..."}

Do not include markdown, code fences, or any text outside the JSON object.
The category must be one of the four allowed categories.

EXAMPLES:
Example 1 (billing): {"category": "billing", "reason": "The customer was charged twice for one order."}
Example 2 (delivery): {"category": "delivery", "reason": "The customer's order arrived late."}
Example 3 (fraud): {"category": "fraud", "reason": "The customer reports an unauthorized transaction."}
""".strip()

def load_tickets(path: Path = TICKETS_PATH) -> pd.DataFrame:
    tickets = pd.read_csv(path)

    required_columns = {
        "ticket_id",
        "customer_id",
        "order_id",
        "text",
        "true_category",
    }

    missing = required_columns - set(tickets.columns)
    if missing:
        raise ValueError(f"Missing required ticket columns: {sorted(missing)}")

    tickets["text"] = tickets["text"].fillna("").astype(str)

    return tickets

def redact_pii(text: str) -> tuple[str, dict[str, int]]:
    """Redact email addresses, phone numbers, and order IDs in order."""

    counts = {
        "emails": 0,
        "phones": 0,
        "order_ids": 0,
    }

    text, counts["emails"] = re.subn(
        r"[\w.+-]+@[\w-]+\.[\w.]+",
        "[EMAIL]",
        text,
    )

    text, counts["phones"] = re.subn(
        r"\b[6-9]\d{9}\b",
        "[PHONE]",
        text,
    )

    text, counts["order_ids"] = re.subn(
        r"ORD-\d{6}",
        "[ORDER_ID]",
        text,
    )

    return text, counts

def check_input_guardrail(text: str) -> tuple[str | None, int]:

    if not text.strip():
        return "skipped_empty", 0

    estimated_tokens = mock_llm.est_tokens(text)

    if estimated_tokens > MAX_INPUT_TOKENS:
        return "flagged_long", estimated_tokens

    return None, estimated_tokens

def prepare_tickets(tickets: pd.DataFrame) -> pd.DataFrame:
    results = []

    for row in tickets.to_dict(orient="records"):
        status, estimated_tokens = check_input_guardrail(row["text"])
        redacted_text, redaction_counts = redact_pii(row["text"])

        results.append({
            "ticket_id": row["ticket_id"],
            "customer_id": row["customer_id"],
            "text": redacted_text,
        
            "redaction_counts": redaction_counts,
            "true_category": row["true_category"],
            "estimated_tokens": estimated_tokens,
            "status": status or "eligible",
        })

    return pd.DataFrame(results)

def build_user_message(redacted_text: str) -> dict[str, str]:
    """Build a model user message containing only redacted ticket text."""
    return {
        "role": "user",
        "content": redacted_text,
    }


def main() -> None:
    tickets = load_tickets()
    results = prepare_tickets(tickets)
    assert results["text"].notna().all()
    patterns = [
        r"[\w.+-]+@[\w-]+\.[\w.]+",
        r"\b[6-9]\d{9}\b",
        r"ORD-\d{6}",
    ]
    for text in results["text"]:
        for pattern in patterns:
            assert not re.search(pattern, text), (
                f"PII remains after redaction: {pattern}"
            )
    print("PII redaction assertion: PASS")
    totals = {"emails": 0, "phones": 0, "order_ids": 0}
    for counts in results["redaction_counts"]:
        for key, value in counts.items():
            totals[key] += value
    print("Redaction counts:", totals)
    print("Total redactions:", sum(totals.values()))
    assert totals == {"emails": 55, "phones": 91, "order_ids": 132}
    assert len(results) == 164
    assert (results["status"] == "skipped_empty").sum() == 4
    assert (results["status"] == "flagged_long").sum() == 4
    assert (results["status"] == "eligible").sum() == 156
    assert results["ticket_id"].tolist() == tickets["ticket_id"].tolist(), "Ticket order changed!"

    print("Total tickets:", len(results))
    print("Skipped empty:", (results["status"] == "skipped_empty").sum())
    print("Flagged long:", (results["status"] == "flagged_long").sum())
    print("Eligible:", (results["status"] == "eligible").sum())


    # Run the model only for eligible tickets.
    eligible_tickets = results[
        results["status"] == "eligible"
    ]

    # Reset immediately before the full model run.
    mock_llm.reset()

    successful_calls = 0

    for row in eligible_tickets.to_dict(orient="records"):
        messages = [
            {
                "role": "system",
                "content": FEW_SHOT_PROMPT,
            },
            build_user_message(row["text"]),
        ]

        response = call_with_retries(
            row["ticket_id"],
            messages,
        )

        assert response.choices[0].message.content is not None
        successful_calls += 1

    print("Successful model calls:", successful_calls)
    assert successful_calls == 156

if __name__ == "__main__":
    main()
