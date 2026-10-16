import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "instamart.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Checkpoint 1: Cleaned orders count
assert cursor.execute(
    "SELECT COUNT(*) FROM orders"
).fetchone()[0] == 12309

# Checkpoint 2: Unique order IDs
assert cursor.execute(
    "SELECT COUNT(DISTINCT order_id) FROM orders"
).fetchone()[0] == 12309

# Checkpoint 3: Completed orders
assert cursor.execute(
    "SELECT COUNT(*) FROM orders WHERE status = 'completed'"
).fetchone()[0] == 11110

# Checkpoint 4: Cancelled orders
assert cursor.execute(
    "SELECT COUNT(*) FROM orders WHERE status = 'cancelled'"
).fetchone()[0] == 1199

# Checkpoint 5: No pending orders
assert cursor.execute(
    "SELECT COUNT(*) FROM orders WHERE status = 'pending'"
).fetchone()[0] == 0

# Checkpoint 6: No missing order amounts
assert cursor.execute(
    "SELECT COUNT(*) FROM orders WHERE order_amount IS NULL"
).fetchone()[0] == 0

# Checkpoint 7: Completed orders have no missing delivery times
assert cursor.execute(
    "SELECT COUNT(*) FROM orders WHERE status = 'completed' AND delivery_minutes IS NULL"
).fetchone()[0] == 0

# Checkpoint 8: Cancelled orders have missing delivery times
assert cursor.execute(
    "SELECT COUNT(*) FROM orders WHERE status = 'cancelled' AND delivery_minutes IS NULL"
).fetchone()[0] == 1199

# Checkpoint 9: Completed order revenue
revenue = cursor.execute(
    "SELECT ROUND(SUM(order_amount), 2) FROM orders WHERE status = 'completed'"
).fetchone()[0]

assert revenue is not None and abs(revenue - 2998668.80) < 0.01

conn.close()

print("ALL CHECKPOINTS PASSED")