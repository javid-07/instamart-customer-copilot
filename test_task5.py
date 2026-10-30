from src.triage_tickets import validate_response

# Test 1: Valid JSON with allowed category
status, category = validate_response(
    '{"category": "billing", "reason": "Incorrect charge"}'
)
assert status == "classified_json"
assert category == "billing"

# Test 2: Chatty response with one category
status, category = validate_response(
    "The customer appears to have a billing-related problem."
)
assert status == "classified_keyword"
assert category == "billing"

# Test 3: Valid JSON with unsupported category
status, category = validate_response(
    '{"category": "shipping", "reason": "Parcel movement"}'
)
assert status == "flagged_invalid_output"
assert category is None

# Test 4: Multiple category words
status, category = validate_response(
    "The issue involves billing and delivery."
)
assert status == "flagged_invalid_output"
assert category is None

print("Task 5 validation unit tests: PASS")
print("Valid JSON: PASS")
print("Keyword extraction: PASS")
print("Unsupported category: PASS")
print("Ambiguous response: PASS")