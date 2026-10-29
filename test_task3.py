from src.triage_tickets import ZERO_SHOT_PROMPT, FEW_SHOT_PROMPT

categories = ["billing", "delivery", "technical", "fraud"]
json_format = '{"category": "...", "reason": "..."}'

assert "CLASSIFY" in ZERO_SHOT_PROMPT
assert "CLASSIFY" in FEW_SHOT_PROMPT

assert all(category in ZERO_SHOT_PROMPT for category in categories)
assert all(category in FEW_SHOT_PROMPT for category in categories)

assert json_format in ZERO_SHOT_PROMPT
assert json_format in FEW_SHOT_PROMPT

assert "EXAMPLES:" not in ZERO_SHOT_PROMPT
assert any(line.strip() == "EXAMPLES:" for line in FEW_SHOT_PROMPT.splitlines())

examples = [
    line for line in FEW_SHOT_PROMPT.splitlines()
    if line.strip().startswith("Example ")
]
assert len(examples) >= 2
assert any("(fraud)" in line for line in examples)

print("Task 3 prompt checks: PASS")
print("Zero-shot prompt: PASS")
print(f"Few-shot examples: {len(examples)}")
print("Fraud example: PASS")
print("JSON format: PASS")