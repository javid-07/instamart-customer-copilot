from src.triage_tickets import (
    load_tickets,
    prepare_tickets,
    build_user_message,
    call_with_retries,
    FEW_SHOT_PROMPT,
    mock_llm,
)

tickets = load_tickets()
results = prepare_tickets(tickets)

eligible = results[results["status"] == "eligible"]

assert len(eligible) == 156

messages_to_send = [
    [
        {"role": "system", "content": FEW_SHOT_PROMPT},
        build_user_message(row["text"]),
    ]
    for row in eligible.to_dict(orient="records")
]

# Reset immediately before the full model run.
mock_llm.reset()

successful_calls = 0

for row, messages in zip(
    eligible.to_dict(orient="records"),
    messages_to_send,
):
    response = call_with_retries(row["ticket_id"], messages)
    assert response.choices[0].message.content
    successful_calls += 1

print("Eligible tickets:", len(eligible))
print("Successful model responses:", successful_calls)
print("Retry recovery test: PASS")

assert successful_calls == 156