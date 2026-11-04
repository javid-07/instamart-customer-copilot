from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "data" / "policies"
DB_PATH = ROOT / "data" / "instamart.db"
OUTPUT_DIR = ROOT / "outputs"
REFUND_LEDGER = OUTPUT_DIR / "refund_ledger.jsonl"

def get_order(order_id):
    """Retrieve an order from the Instamart database."""

    import sqlite3

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        row = connection.execute(
            "SELECT * FROM orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()

        if row is None:
            return {
                "error": f"Order {order_id} not found."
            }

        return dict(row)

    finally:
        connection.close()

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

def search_policy(query):
    """Search policy documents and return matching results."""

    results = retrieve(query, k=3)

    return {
        "results": results
    }

def calculate_refund(order_amount, delivery_minutes):
    """Calculate refund based on the late-delivery policy."""

    if delivery_minutes > 45:
        refund_inr = round(float(order_amount), 2)
    else:
        refund_inr = 0.0

    return {
        "refund_inr": refund_inr
    }

def issue_refund(order_id, refund_inr):
    """Record an issued refund in the JSONL ledger."""

    import json
    from datetime import datetime, timezone

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ledger_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": "issue_refund",
        "order_id": order_id,
        "refund_inr": round(float(refund_inr), 2),
    }

    with REFUND_LEDGER.open("a", encoding="utf-8") as file:
        file.write(json.dumps(ledger_entry) + "\n")

    return {
        "order_id": order_id,
        "refund_inr": ledger_entry["refund_inr"],
        "status": "issued",
    }

def escalate_to_human(order_id, refund_inr):
    """Record a refund escalation for human approval."""

    import json
    from datetime import datetime, timezone

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ledger_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": "escalate_to_human",
        "order_id": order_id,
        "refund_inr": round(float(refund_inr), 2),
    }

    with REFUND_LEDGER.open("a", encoding="utf-8") as file:
        file.write(json.dumps(ledger_entry) + "\n")

    return {
        "order_id": order_id,
        "refund_inr": ledger_entry["refund_inr"],
        "status": "escalated",
    }

TOOLS_SPEC = [
    {
        "name": "get_order",
        "description": "Retrieve order details using an order ID.",
        "parameters": {
            "order_id": "string"
        },
    },
    {
        "name": "search_policy",
        "description": "Search policy documents and retrieve relevant policy chunks.",
        "parameters": {
            "query": "string"
        },
    },
    {
        "name": "calculate_refund",
        "description": "Calculate the refund amount based on order amount and delivery time.",
        "parameters": {
            "order_amount": "number",
            "delivery_minutes": "number"
        },
    },
    {
        "name": "issue_refund",
        "description": "Record an approved refund in the refund ledger.",
        "parameters": {
            "order_id": "string",
            "refund_inr": "number"
        },
    },
    {
        "name": "escalate_to_human",
        "description": "Record a refund request requiring human approval.",
        "parameters": {
            "order_id": "string",
            "refund_inr": "number"
        },
    },
]


TOOL_MAP = {
    "get_order": get_order,
    "search_policy": search_policy,
    "calculate_refund": calculate_refund,
    "issue_refund": issue_refund,
    "escalate_to_human": escalate_to_human,
}

def answer(question):
    """Answer a policy question using retrieved context."""

    import sys
    sys.path.insert(0, str(ROOT))

    import mock_llm

    sources = retrieve(question, k=3)

    # Ignore irrelevant chunks with zero similarity.
    sources = [
        item for item in sources
        if item["score"] > 0
    ]

    context_parts = []

    for item in sources:
        context_parts.append(
            f"[{item['source']}]\n{item['text']}"
        )

    user_message = (
        "CONTEXT:\n"
        + "\n".join(context_parts)
        + "\nQUESTION:\n"
        + question
    )

    messages = [
        {
            "role": "system",
            "content": (
                "POLICY ASSISTANT. Answer the question using only "
                "the supplied policy context. Do not use outside "
                "knowledge or make assumptions. If the information "
                "is not available in the context, say that you "
                "could not find the information in the policy documents."
            ),
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    response = mock_llm.chat(messages)

    return {
        "answer": response.choices[0].message.content,
        "sources": [item["source"] for item in sources],
    }

def evaluate_policy(overlap=10):
    """Evaluate policy retrieval and answer accuracy."""

    import csv

    global CHUNKS, CHUNK_TEXTS, VECTORIZER, TFIDF_MATRIX

    # Build the index using the requested overlap.
    CHUNKS = chunk_documents(chunk_size=40, overlap=overlap)
    CHUNK_TEXTS = [chunk["text"] for chunk in CHUNKS]

    VECTORIZER = TfidfVectorizer()
    TFIDF_MATRIX = VECTORIZER.fit_transform(CHUNK_TEXTS)

    results = []

    eval_file = ROOT / "data" / "raw" / "policy_eval.csv"

    with eval_file.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            question = row["question"]
            expected_doc = row["expected_doc"]
            expected_fact = row["expected_fact"]

            retrieved = retrieve(question, k=3)
            response = answer(question)
            answer_text = response["answer"]

            if expected_doc == "NONE":
                passed = answer_text.startswith("I could not find")
                doc_match = None
                fact_match = None
            else:
                doc_match = expected_doc in [
                    item["source"] for item in retrieved
                ]
                fact_match = expected_fact in answer_text
                passed = doc_match and fact_match

            results.append({
                "question": question,
                "expected_doc": expected_doc,
                "doc_match": doc_match,
                "fact_match": fact_match,
                "passed": passed,
            })

    return results

def run_agent(
    user_message,
    scenario_id,
    max_iterations=6,
    token_limit=6000,
    time_limit_seconds=10,
):
    """Run a ReAct agent with iteration, token and time limits."""

    import json
    import time
    import mock_llm

    start_time = time.monotonic()

    messages = [
        {
            "role": "system",
            "content": (
                "AGENT. You are an Instamart refund support agent. "
                "Use the available tools to retrieve orders, search "
                "policies, calculate refunds, issue eligible refunds, "
                "and escalate refunds above INR 1000. "
                "Only completed orders are refundable."
            ),
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    steps = []
    llm_calls = 0
    tokens_used = 0
    status = "COMPLETED"
    final_answer = ""

    for iteration in range(max_iterations):

        # Check timeout before every model call.
        elapsed = time.monotonic() - start_time

        if elapsed >= time_limit_seconds:
            status = "FALLBACK_TIMEOUT"
            final_answer = (
                "Human handoff required: agent time limit reached. "
                f"Completed {len(steps)} tool executions."
            )
            break

        response = mock_llm.chat(messages, tools=TOOLS_SPEC)

        llm_calls += 1
        tokens_used += response.usage.total_tokens

        # Stop immediately if the token budget is exceeded.
        # Do not execute any tool requested by this response.
        if tokens_used > token_limit:
            status = "FALLBACK_TOKEN_LIMIT"
            final_answer = (
                "Human handoff required: token budget exceeded. "
                f"Completed {len(steps)} tool executions."
            )
            break

        assistant_message = response.choices[0].message

        if response.choices[0].finish_reason != "tool_calls":
            final_answer = assistant_message.content or ""
            break

        messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [
                {
                    "id": call.id,
                    "name": call.name,
                    "arguments": call.arguments,
                }
                for call in assistant_message.tool_calls
            ],
        })

        for call in assistant_message.tool_calls:
            tool_name = call.name
            arguments = call.arguments

            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            tool_function = TOOL_MAP.get(tool_name)

            if tool_function is None:
                observation = {
                    "error": f"Unknown tool: {tool_name}"
                }
            else:
                observation = tool_function(**arguments)

            steps.append({
                "tool": tool_name,
                "args": arguments,
                "observation": observation,
            })

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": tool_name,
                "content": json.dumps(observation),
            })

    else:
        status = "FALLBACK_MAX_ITERATIONS"
        final_answer = (
            "Human handoff required: maximum agent iterations reached. "
            f"Completed {len(steps)} tool executions."
        )

    # Assign business outcome only when no safety fallback occurred.
    if status == "COMPLETED":
        if final_answer.startswith("REFUND:"):
            status = "REFUND"
        elif final_answer.startswith("ESCALATE:"):
            status = "ESCALATE"
        elif final_answer.startswith("DENIED:"):
            status = "DENIED"
        elif final_answer.startswith("NOT_FOUND:"):
            status = "NOT_FOUND"
        elif final_answer.startswith("NEEDS_INFO:"):
            status = "NEEDS_INFO"

    return {
        "scenario_id": scenario_id,
        "status": status,
        "final_answer": final_answer,
        "steps": steps,
        "llm_calls": llm_calls,
        "tokens_used": tokens_used,
    }

def save_agent_run(result):
    """Append one agent execution record to a JSONL file."""

    import json

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / "agent_runs.jsonl"

    record = {
        "scenario_id": result["scenario_id"],
        "status": result["status"],
        "final_answer": result["final_answer"],
        "llm_calls": result["llm_calls"],
        "tokens_used": result["tokens_used"],
        "steps": result["steps"],
    }

    with output_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")

    return record

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
