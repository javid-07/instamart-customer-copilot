# Instamart Customer Intelligence & Support Copilot

## Overview

This project builds a customer intelligence and support copilot using synthetic data. It includes data cleaning, customer segmentation, lapse prediction, ticket triage, policy question answering and refund processing.

## Reproduce

1. Clone the repository: `git clone https://github.com/javid-07/instamart-customer-copilot.git`
2. Enter the project directory: `cd instamart-customer-copilot`
3. Create a virtual environment using Python 3.11: `python -m venv .venv`
4. Activate the virtual environment in PowerShell: `.\.venv\Scripts\Activate.ps1`
5. Install dependencies: `python -m pip install -r requirements.txt`
6. Generate the synthetic data: `python generate_data.py`

Expected generator output:

`generated: customers=1200 products=40 orders_raw=13084 tickets=164`

## Part A — Data Foundation

### Task 1: Reproducible Setup

The project environment was configured using Python 3.11. Dependencies were installed using `requirements.txt`, and the synthetic data generation script was executed successfully. The setup was also tested in a fresh clone.

### Task 2: Raw Data Audit

The raw customers, products, and orders datasets were inspected using pandas. The audit reports each dataset's shape, column data types, missing-value counts, missing-value percentages, and exact duplicate rows.

#### Raw Dataset Summary

| Dataset | Rows | Columns | Exact Duplicate Rows |
|---|---:|---:|---:|
| Customers | 1,200 | 5 | 0 |
| Products | 40 | 4 | 0 |
| Orders | 13,084 | 9 | 119 |

#### Customers: Column Audit

| Column | Data Type | Missing Count | Missing Percentage |
|---|---|---:|---:|
| `customer_id` | string | 0 | 0.00% |
| `city` | string | 0 | 0.00% |
| `signup_date` | string | 0 | 0.00% |
| `age` | float64 | 61 | 5.08% |
| `gender` | string | 30 | 2.50% |

#### Products: Column Audit

| Column | Data Type | Missing Count | Missing Percentage |
|---|---|---:|---:|
| `product_id` | string | 0 | 0.00% |
| `product_name` | string | 0 | 0.00% |
| `category` | string | 0 | 0.00% |
| `price_inr` | int64 | 0 | 0.00% |

#### Orders: Column Audit

| Column | Data Type | Missing Count | Missing Percentage |
|---|---|---:|---:|
| `order_id` | string | 0 | 0.00% |
| `customer_id` | string | 0 | 0.00% |
| `product_id` | string | 0 | 0.00% |
| `quantity` | int64 | 0 | 0.00% |
| `order_ts` | string | 0 | 0.00% |
| `status` | string | 0 | 0.00% |
| `discount_pct` | int64 | 0 | 0.00% |
| `order_amount` | string | 53 | 0.41% |
| `delivery_minutes` | float64 | 2,541 | 19.42% |

#### Specific Audit Figures

| Audit Metric | Result |
|---|---:|
| Raw orders rows | 13,084 |
| Exact duplicate order rows | 119 |
| Rows with pending status | 656 |
| Distinct `order_id` values | 12,309 |
| Non-numeric `order_amount` entries | 120 |
| Negative `delivery_minutes` values | 106 |
| Blank `delivery_minutes` values | 2,541 |
| Blank customer age values | 61 |
| Customer ages outside 10–100 | 6 |
| Distinct raw city spellings | 24 |
| Distinct non-blank raw gender spellings | 10 |
| Blank gender values | 30 |

These findings establish the baseline for the subsequent data-cleaning and validation tasks.

### Task 3: Clean Orders

The raw orders dataset was cleaned using pandas in the following order:

1. Converted `order_ts` to datetime format.
2. Removed exact duplicate rows.
3. Sorted orders by timestamp and kept the latest record for each `order_id`.
4. Converted `order_amount` to numeric values. Unparseable or missing amounts were filled using the formula:

   `order_amount = round(price_inr * quantity * (1 - discount_pct / 100), 2)`

5. Set negative `delivery_minutes` values to missing.
6. Filled missing delivery times for completed orders using the median delivery time for the corresponding product category, calculated from completed orders with valid delivery times.
7. Kept delivery times missing for cancelled orders because those orders were not delivered.

#### Cleaning Results

| Checkpoint | Expected Result | Actual Result |
|---|---:|---:|
| Total cleaned orders | 12,309 | 12,309 |
| Completed orders | 11,110 | 11,110 |
| Cancelled orders | 1,199 | 1,199 |
| Pending orders | 0 | 0 |
| Missing order amounts | 0 | 0 |
| Completed orders with missing delivery time | 0 | 0 |
| Cancelled orders with missing delivery time | 1,199 | 1,199 |
| Total completed order amount | INR 2,998,668.80 | INR 2,998,668.80 |

The cleaning results match the assignment's reference checkpoints.

### Task 3: Clean Customers

The raw customers dataset was cleaned using pandas with the following steps:

1. Standardized city names by removing leading and trailing spaces and converting them to title case.
2. Standardized gender values into `female`, `male`, and `unknown`.
3. Replaced invalid ages outside the range of 10–100 with missing values.
4. Filled missing ages using the median age of the corresponding city.
5. Converted `signup_date` to datetime format.
6. Saved the cleaned dataset to `data/clean/customers.csv`.

#### Cleaning Results

| Checkpoint | Actual Result |
|---|---:|
| Total customers | 1,200 |
| Pune | 227 |
| Delhi | 210 |
| Bengaluru | 197 |
| Chennai | 191 |
| Hyderabad | 191 |
| Mumbai | 184 |
| Female | 610 |
| Male | 560 |
| Unknown gender | 30 |
| Missing ages | 0 |
| Minimum age | 18 |
| Maximum age | 60 |
| Missing signup dates | 0 |

### Task 3: Clean Products

The products dataset was validated using pandas. The schema was checked, product IDs were verified for uniqueness, missing values were checked, and product prices were validated to ensure they were positive.

The cleaned dataset was saved to `data/clean/products.csv`.

#### Cleaning Results

| Checkpoint | Actual Result |
|---|---:|
| Total products | 40 |
| Unique product IDs | 40 |
| Missing values | 0 |
| Non-positive product prices | 0 |

### Task 5: Store and Validate

#### SQLite Database

The cleaned customers, products, and orders datasets were stored in a SQLite database at `data/instamart.db`.

| Table | Rows |
|---|---:|
| `customers` | 1,200 |
| `products` | 40 |
| `orders` | 12,309 |

The `order_ts` column is stored in the `YYYY-MM-DD HH:MM:SS` format.

#### Data Validation

A validation script, `validate_data.py`, was created to verify nine checkpoints covering cleaned order counts, unique order IDs, order statuses, missing order amounts, delivery times, and completed order revenue.

Run the validation script using:

```bash
python validate_data.py
```

Expected output:

```text
ALL CHECKPOINTS PASSED
```

All nine validation checkpoints passed successfully.
