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

### Task 2: Raw Data Audit

The raw customers, products, and orders datasets were inspected using pandas. The audit reports each dataset's shape, column data types, missing-value counts, missing-value percentages, and exact duplicate rows.

#### Raw Dataset Summary

| Dataset | Rows | Columns | Exact Duplicate Rows |
|---|---:|---:|---:|
| Customers | 1,200 | 5 | 0 |
| Products | 40 | 4 | 0 |
| Orders | 13,084 | 9 | 119 |

#### Key Audit Findings

- **Orders:** 13,084 raw rows, 119 exact duplicate rows, 656 pending orders, and 12,309 distinct order IDs.
- **Order amounts:** 120 entries could not be converted to numeric values.
- **Delivery time:** 106 negative values and 2,541 blank or missing values.
- **Customers:** 61 missing age values and 6 age values outside the 10–100 range.
- **City:** 24 distinct raw city spellings were found.
- **Gender:** 10 distinct non-blank raw spellings and 30 blank values were found.

These findings establish the baseline for the subsequent data-cleaning and validation tasks.