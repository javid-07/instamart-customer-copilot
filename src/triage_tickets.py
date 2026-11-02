import sys
from pathlib import Path
import re
import pandas as pd
import random
import time
import json

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

def validate_response(response_text):
    """Validate JSON output or extract one unambiguous category keyword."""

    allowed_categories = {
        "billing",
        "delivery",
        "technical",
        "fraud",
    }

    # First, try parsing the response as JSON.
    try:
        data = json.loads(response_text)

        if (
            isinstance(data, dict)
            and data.get("category") in allowed_categories
        ):
            return "classified_json", data["category"]

        # Valid JSON with an unsupported category must be flagged.
        return "flagged_invalid_output", None

    except json.JSONDecodeError:
        pass

    # If JSON parsing fails, extract lowercase words.
    words = re.findall(r"[a-z]+", response_text.lower())

    matched_categories = allowed_categories.intersection(words)

    if len(matched_categories) == 1:
        category = matched_categories.pop()
        return "classified_keyword", category

    return "flagged_invalid_output", None

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


def run_classification(
    eligible_tickets,
    prompt,
    token_budget=100000,
):
    """Run classification with a token budget."""

    mock_llm.reset()

    run_results = []
    total_tokens = 0

    for row in eligible_tickets.to_dict(orient="records"):

        # Check budget before making a model call.
        if total_tokens >= token_budget:
            run_results.append({
                "ticket_id": row["ticket_id"],
                "true_category": row["true_category"],
                "predicted_category": None,
                "status": "budget_exhausted",
                "tokens_used": 0,
            })
            continue

        messages = [
            {
                "role": "system",
                "content": prompt,
            },
            build_user_message(row["text"]),
        ]

        response = call_with_retries(
            row["ticket_id"],
            messages,
        )

        response_text = response.choices[0].message.content
        status, category = validate_response(response_text)

        tokens_used = response.usage.total_tokens
        total_tokens += tokens_used

        run_results.append({
            "ticket_id": row["ticket_id"],
            "true_category": row["true_category"],
            "predicted_category": category,
            "status": status,
            "tokens_used": tokens_used,
        })

    return pd.DataFrame(run_results), total_tokens


def build_routing_output(results, run_results, segments):
    """Merge ticket classifications with customer segments and assign routes."""

    output = results[
        ["ticket_id", "customer_id", "status"]
    ].copy()

    output = output.merge(
        run_results[
            ["ticket_id", "predicted_category", "status", "tokens_used"]
        ],
        on="ticket_id",
        how="left",
        suffixes=("", "_model"),
    )

    # Use model status for tickets that reached classification.
    output["status"] = output["status_model"].combine_first(
        output["status"]
    )

    output = output.drop(columns=["status_model"])

    output = output.merge(
        segments[["customer_id", "segment_name", "is_premium"]],
        on="customer_id",
        how="left",
    )

    output["category"] = output["predicted_category"].fillna("")
    output["segment_name"] = output["segment_name"].fillna("")
    output["tokens_used"] = output["tokens_used"].fillna(0).astype(int)

    def assign_routing(row):
        if row["status"] in {
            "skipped_empty",
            "flagged_long",
            "flagged_invalid_output",
            "budget_exhausted",
        }:
            return "NORMAL", "human_review"

        if row["category"] == "fraud":
            return "HIGH", "security_team"

        if row["is_premium"] == True:
            return "HIGH", "premium_desk"

        return "NORMAL", "support_queue"

    output[["priority", "route"]] = output.apply(
        lambda row: pd.Series(assign_routing(row)),
        axis=1,
    )

    return output[
        [
            "ticket_id",
            "customer_id",
            "status",
            "category",
            "segment_name",
            "priority",
            "route",
            "tokens_used",
        ]
    ]


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

    assert totals == {
        "emails": 55,
        "phones": 91,
        "order_ids": 132,
    }

    assert len(results) == 164
    assert (results["status"] == "skipped_empty").sum() == 4
    assert (results["status"] == "flagged_long").sum() == 4
    assert (results["status"] == "eligible").sum() == 156

    assert results["ticket_id"].tolist() == tickets["ticket_id"].tolist(), (
        "Ticket order changed!"
    )

    print("Total tickets:", len(results))
    print("Skipped empty:", (results["status"] == "skipped_empty").sum())
    print("Flagged long:", (results["status"] == "flagged_long").sum())
    print("Eligible:", (results["status"] == "eligible").sum())

    # Run both classification prompts.
    eligible_tickets = results[
        results["status"] == "eligible"
    ]

    print("\n========== ZERO-SHOT RUN ==========")

    zero_shot_results, zero_shot_tokens = run_classification(
        eligible_tickets,
        ZERO_SHOT_PROMPT,
    )

    print("\n========== FEW-SHOT RUN ==========")

    few_shot_results, few_shot_tokens = run_classification(
        eligible_tickets,
        FEW_SHOT_PROMPT,
    )

    # Calculate classification metrics.
    def calculate_metrics(run_results, total_tokens):
        classified = run_results[
            run_results["status"].isin(
                ["classified_json", "classified_keyword"]
            )
        ]

        correct = (
            classified["true_category"]
            == classified["predicted_category"]
        ).sum()

        classified_count = len(classified)

        accuracy = (
            correct / classified_count * 100
            if classified_count else 0
        )

        tokens_per_ticket = (
            total_tokens / classified_count
            if classified_count else 0
        )

        return {
            "classified": classified_count,
            "correct": int(correct),
            "accuracy": accuracy,
            "total_tokens": total_tokens,
            "tokens_per_ticket": tokens_per_ticket,
        }

    zero_metrics = calculate_metrics(
        zero_shot_results,
        zero_shot_tokens,
    )

    few_metrics = calculate_metrics(
        few_shot_results,
        few_shot_tokens,
    )

    print("\n========== TASK 6 COMPARISON ==========")

    print("\nZero-shot metrics:")
    for key, value in zero_metrics.items():
        print(f"{key}: {value}")

    print("\nFew-shot metrics:")
    for key, value in few_metrics.items():
        print(f"{key}: {value}")

    # Zero-shot confusion matrix.
    zero_classified = zero_shot_results[
        zero_shot_results["status"].isin(
            ["classified_json", "classified_keyword"]
        )
    ]

    confusion_matrix = pd.crosstab(
        zero_classified["true_category"],
        zero_classified["predicted_category"],
        rownames=["Actual"],
        colnames=["Predicted"],
        dropna=False,
    )

    print("\nZero-shot confusion matrix:")
    print(confusion_matrix)

    #Task7
    segments = pd.read_csv(
        ROOT / "outputs" / "customer_segments.csv"
    )

    # Zero-shot budget demonstration.
    print("\n========== BUDGET DEMO RUN ==========")

    budget_demo_results, budget_demo_tokens = run_classification(
        eligible_tickets,
        ZERO_SHOT_PROMPT,
        token_budget=6000,
    )

    budget_exhausted_count = (
        budget_demo_results["status"] == "budget_exhausted"
    ).sum()

    print("Demo token budget: 6000")
    print("Total tokens used:", budget_demo_tokens)
    print("Budget exhausted tickets:", budget_exhausted_count)

    assert budget_exhausted_count > 0, (
        "No tickets exhausted the budget. Try a lower demo budget."
    )

    budget_demo_output = build_routing_output(
        results,
        budget_demo_results,
        segments,
    )

    output_dir = ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    budget_demo_output.to_csv(
        output_dir / "triage_budget_demo.csv",
        index=False,
    )

    print("Saved: outputs/triage_budget_demo.csv")

    # Final few-shot run with a large token budget.
    print("\n========== FINAL TRIAGE RUN ==========")

    final_results, final_tokens = run_classification(
        eligible_tickets,
        FEW_SHOT_PROMPT,
        token_budget=100000,
    )

    print("Final token budget: 100000")
    print("Total tokens used:", final_tokens)

    final_output = build_routing_output(
        results,
        final_results,
        segments,
    )

    final_output.to_csv(
        output_dir / "triage_results.csv",
        index=False,
    )

    print("Saved: outputs/triage_results.csv")
    print("\nFinal routing counts:")
    print(final_output["route"].value_counts())

    assert len(final_output) == 164
    assert list(final_output.columns) == [
        "ticket_id",
        "customer_id",
        "status",
        "category",
        "segment_name",
        "priority",
        "route",
        "tokens_used",
    ]
    assert not (final_output["status"] == "budget_exhausted").any()


if __name__ == "__main__":
    main()
