# Instamart Customer Intelligence & Support Copilot

## Overview

This project builds a customer intelligence and support copilot using synthetic data. The planned pipeline covers data cleaning and analytics, customer segmentation and lapse prediction, support-ticket triage with privacy guardrails, policy question answering, and refund processing.

All data is synthetic and fictional. Monetary values are reported in Indian Rupees (INR).

## Reproduce

Run these commands from a clean clone, in order, using Python 3.11 or newer.

1. Clone the repository:

   ```bash
   git clone https://github.com/javid-07/instamart-customer-copilot.git
   cd instamart-customer-copilot
   ```

2. Create and activate a virtual environment.

   PowerShell:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   macOS/Linux:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Generate the synthetic raw data:

   ```bash
   python generate_data.py
   ```

   Expected final line:

   ```text
   generated: customers=1200 products=40 orders_raw=13084 tickets=164
   ```

5. Run the Part A cleaning scripts:

   ```bash
   python src/clean_orders.py
   python src/clean_customers.py
   python src/clean_products.py
   ```

6. Create the SQLite database and run the validation checks:

   ```bash
   python create_database.py
   python validate_data.py
   ```

   Expected validation output:

   ```text
   ALL CHECKPOINTS PASSED
   ```

7. Run the SQL and pandas analyses:

   ```bash
   python src/pandas_analysis.py
   ```

   The seven SQL statements are stored in `sql/queries.sql` and were run against `data/instamart.db` using `pandas.read_sql_query` during verification.

## Part A : Data Foundation: Clean, Store, Query

### Task 1: Reproducible Setup

The project environment was configured using Python 3.11. Dependencies were installed using `requirements.txt`, and the supplied synthetic data generator was executed successfully. The setup was also tested in a fresh clone. The supplied `generate_data.py` and `mock_llm.py` files are kept unmodified.

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
| Customer ages outside 10â€“100 | 6 |
| Distinct raw city spellings | 24 |
| Distinct non-blank raw gender spellings | 10 |
| Blank gender values | 30 |

These findings establish the baseline for the subsequent data-cleaning and validation tasks.

### Task 3: Clean Orders

The raw orders dataset was cleaned using pandas in the following order:

1. Converted `order_ts` to datetime format.
2. Removed exact duplicate rows.
3. Sorted orders by timestamp and kept the latest record for each `order_id`.
4. Converted `order_amount` to numeric values, turning unparseable entries into missing values. Missing amounts were filled using:

   `order_amount = round(price_inr * quantity * (1 - discount_pct / 100), 2)`

5. Set negative `delivery_minutes` values to missing.
6. Filled missing delivery times for completed orders using the median delivery time for the corresponding product category, calculated from completed orders with valid delivery times.
7. Kept delivery times missing for cancelled orders because those orders were not delivered.

#### Cleaning Transformation Counts

Counts below are measured at the relevant stage of the cleaning pipeline, after the preceding transformation where applicable.

| Transformation | Rows or values affected |
|---|---:|
| Exact duplicate rows removed | 119 |
| Duplicate `order_id` records removed after exact deduplication | 656 |
| Missing/invalid `order_amount` values after numeric conversion | 112 |
| Missing `order_amount` values filled using product price, quantity, and discount | 112 |
| Negative delivery times identified after deduplication | 105 |
| Completed-order delivery times filled using category median | 774 |

#### Cleaning Results

| Checkpoint | Expected Result | Actual Result |
|---|---:|---:|
| Total cleaned orders | 12,309 | 12,309 |
| Distinct order IDs | 12,309 | 12,309 |
| Completed orders | 11,110 | 11,110 |
| Cancelled orders | 1,199 | 1,199 |
| Pending orders | 0 | 0 |
| Missing order amounts | 0 | 0 |
| Completed orders with missing delivery time | 0 | 0 |
| Cancelled orders with missing delivery time | 1,199 | 1,199 |
| Total completed order amount | INR 2,998,668.80 | INR 2,998,668.80 |

The cleaning results match the assignment's reference checkpoints.

### Task 4: Clean Customers and Products

#### Customers

The raw customers dataset was cleaned using pandas:

1. Standardized city names by removing leading and trailing spaces and converting them to title case.
2. Standardized gender values into `female`, `male`, and `unknown`.
3. Replaced invalid ages outside the range of 10â€“100 with missing values.
4. Filled missing ages using the median age of the corresponding city.
5. Converted `signup_date` to datetime format.
6. Saved the cleaned dataset to `data/clean/customers.csv`.

##### Cleaning Transformation Counts

| Transformation | Rows or values affected |
|---|---:|
| City values changed by standardization | 476 |
| Gender values changed by standardization | 950 |
| Rows assigned `unknown` gender | 30 |
| Invalid non-missing ages converted to missing | 6 |
| Missing ages before median imputation | 67 |
| Age values filled using city median | 67 |
| Missing/invalid signup dates after conversion | 0 |

The 67 age values filled include both originally missing ages and the six invalid ages; these counts must not be added together.

##### Customer Cleaning Results

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

#### Products

The products dataset was validated using pandas. The schema was checked, product IDs were verified for uniqueness, missing values were checked, and product prices were validated to ensure they were positive. The cleaned dataset was saved to `data/clean/products.csv`.

##### Product Cleaning Results

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

The `order_ts` column is stored as text in the `YYYY-MM-DD HH:MM:SS` format. The generated database is excluded from Git and is recreated by `create_database.py`.

#### Data Validation

The `validate_data.py` script verifies nine checkpoints covering cleaned order counts, unique order IDs, order statuses, missing order amounts, delivery times, and completed-order revenue.

Run the validation script using:

```bash
python validate_data.py
```

Expected output:

```text
ALL CHECKPOINTS PASSED
```

All nine validation checkpoints passed successfully.

### Task 6: SQL Analysis

Seven SQL queries are saved in `sql/queries.sql` and were executed against `data/instamart.db` using Python and `pandas.read_sql_query`. Revenue and customer-spend calculations use completed orders only.

| Query | Analysis | Reference Result | Actual Result |
|---|---|---:|---:|
| Q1 | `WHERE` and `HAVING` | 30 customers | 30 customers |
| Q2 | Three-table join: city and category revenue | 30 rows; INR 2,998,668.80 total | 30 rows; INR 2,998,668.80 total |
| Q3 | Scalar subquery: products above average catalogue price | 11 products | 11 products |
| Q4 | `LEFT JOIN`: customers with no completed orders | 25 customers | 25 customers |
| Q5 | CTE: customers spending above the average | 550 customers; INR 2,552.06 average | 550 customers; INR 2,552.06 average |
| Q6 | `RANK()`, `DENSE_RANK()`, and `ROW_NUMBER()` by city | 8 rows where `RANK()` differs from `ROW_NUMBER()` | 8 rows |
| Q7 | Daily revenue and cumulative running total | 183 days; INR 2,998,668.80 final total | 183 days; INR 2,998,668.80 final total |

The highest city/category revenue was Bengaluru / Electronics at INR 233,909.45. The top-spending customer in each city matched the assignment reference results.

**Ranking note:** When customers tie on total spend, `RANK()` assigns the same rank and may skip subsequent ranks, while `ROW_NUMBER()` assigns a unique sequential number to each row.

### Task 7: Pandas Cross-check and Exploratory Analysis

#### Cross-checks

The city/category revenue pivot table was rebuilt with `pandas.pivot_table(..., margins=True)`. Its grand total matched the SQL revenue total of INR 2,998,668.80.

| City | Completed Revenue Sum | Mean Order Amount | Completed Orders |
|---|---:|---:|---:|
| Bengaluru | INR 523,643.40 | INR 276.47 | 1,894 |
| Mumbai | INR 479,058.50 | INR 297.00 | 1,613 |

#### Exploratory Findings

The dataset contains synthetic Instamart completed-order transactions across six cities and five product categories. The 11,110 completed orders generated total revenue of INR 2,998,668.80.

Order amounts are right-skewed: the mean is INR 269.91, the median is INR 135.00, and skewness is 4.61. The first and third quartiles are INR 64.80 and INR 297.00, respectively. The interquartile range (IQR) is INR 232.20.

Using the 1.5 × IQR rule, the lower fence is INR -283.50 and the upper fence is INR 645.30. There are no lower outliers and 897 upper outliers. These high-value transactions may represent unusually large orders, but they are not necessarily errors.

The strongest absolute correlation is between order amount and discount percentage (approximately -0.095). Order amount and quantity have a smaller positive correlation (+0.087). Both relationships are weak; a correlation of this size does not establish causation.


---

## Part B: Customer Segmentation and Lapse Prediction

### Task 1: RFM Analysis

Built a Recency, Frequency, Monetary (RFM) table using completed orders.

- Snapshot date: 2025-10-01
- Customers with completed orders: 1,175
- Median recency: 19 days
- Recency range: 0–180 days
- Mean frequency: 9.46 orders
- Maximum frequency: 33 orders
- Mean monetary value: INR 2,552.06
- Maximum monetary value: INR 14,766.55

Output: `outputs/rfm.csv`

### Task 2: K-means Clustering

Standardized RFM features and evaluated K-means for K = 2 through 8, using `random_state=42` and `n_init=10`.

| K | Inertia | Silhouette |
|---:|---:|---:|
| 2 | 1820.8 | 0.465 |
| 3 | 1268.2 | 0.445 |
| 4 | 743.1 | 0.526 |
| 5 | 617.4 | 0.480 |
| 6 | 503.2 | 0.482 |
| 7 | 408.5 | 0.416 |
| 8 | 366.5 | 0.412 |

K = 4 was selected because it had the highest silhouette score among the tested values.

Output: `outputs/kmeans_evaluation.csv`

### Task 3: Customer Segment Profiles

| Segment | Customers | Mean Recency (days) | Mean Frequency | Mean Monetary (INR) |
|---|---:|---:|---:|---:|
| 0 | 436 | 28.86 | 3.77 | 1,057.62 |
| 1 | 138 | 24.12 | 6.77 | 7,129.70 |
| 2 | 419 | 8.77 | 19.40 | 3,410.02 |
| 3 | 182 | 109.04 | 2.20 | 685.99 |

Business interpretation:

- Segment 0: Occasional Shoppers
- Segment 1: Premium Spenders
- Segment 2: Loyal Frequent Buyers
- Segment 3: At-Risk Inactive Customers

Segment 1 was selected as the Premium segment because it had the highest mean monetary value. It contains 138 customers.

### Task 4: PCA

Principal Component Analysis was performed on standardized RFM features.

- PC1 explained variance: 0.634
- PC2 explained variance: 0.218
- Total explained variance: 0.852 (85.2%)

Output: `outputs/customer_segments.csv`

### Task 5: Lapse Cohort and Labels

The lapse cohort included customers with at least one completed order before 2025-09-01. A customer was labelled as lapsed if they had no completed order from 2025-09-01 through 2025-09-30.

- Cohort size: 1,156
- Lapsed customers: 443
- Non-lapsed customers: 713
- Lapse rate: 38.32%

Output: `outputs/lapse_dataset.csv`

### Task 6: Leakage-Free Features

Customer features were built using orders before 2025-09-01 only. September activity was used for the target label, not as a model feature.

The dataset contains 1,156 customers, 11 features, and no missing values.

Features include recency, frequency, monetary value, average discount, average delivery time, cancellation rate, favourite category, city, age, gender, and customer tenure.

Output: `outputs/lapse_features.csv`

### Task 7: Lapse Prediction Models

A stratified train/test split was used with `test_size=0.2` and `random_state=42`.

| Metric | Logistic Regression | Random Forest |
|---|---:|---:|
| Best CV F1 | 0.639 | 0.672 |
| Test accuracy | 0.763 | 0.763 |
| Lapsed-class precision | 0.65 | 0.67 |
| Lapsed-class recall | 0.81 | 0.74 |
| Lapsed-class F1 | 0.724 | 0.706 |

Logistic Regression was selected based on its higher test-set F1-score. The selected model was saved and reloaded successfully, and the reloaded predictions matched the original predictions.

Class-balancing experiment:

| Metric | Original Training | Balanced Training |
|---|---:|---:|
| Precision | 0.655 | 0.587 |
| Recall | 0.809 | 0.910 |
| F1-score | 0.724 | 0.714 |

Balancing improved recall but reduced precision. The choice depends on the cost of missed at-risk customers versus unnecessary retention offers.

Random Forest feature importance ranked frequency first (0.401), followed by monetary value (0.257), recency (0.083), cancellation rate (0.083), and average discount (0.055).

### Task 8: Retention List

The selected Logistic Regression model scored the 1,156 customers in the lapse cohort. Customers were ranked by predicted lapse probability, highest risk first.

Output: `outputs/retention_list.csv`

The retention list supports prioritization of re-engagement campaigns. Predicted probabilities are estimates and do not guarantee future customer behaviour.

### Reproducibility and Leakage Checks

- The RFM calculations use completed orders only, with the snapshot set to `2025-10-01 00:00:00`.
- K-means evaluation uses `StandardScaler` and `KMeans(n_init=10, random_state=42)` for each K from 2 through 8. K=8 has lower inertia than K=2 because increasing the number of clusters reduces within-cluster distances; this alone does not identify the best K. The final choice considers the elbow, silhouette score, and whether the resulting segments are useful for business decisions.
- The lapse cohort is defined using completed orders before `2025-09-01`. No orders dated `2025-09-01` onwards are used to build model features, and the Part B segment labels are not used as model features.
- The train/test split uses `test_size=0.2`, `stratify=y`, and `random_state=42`. Preprocessing and resampling are fitted/applied to training data only; the test set remains unchanged for evaluation. The encoder and scaler do not learn from test rows.
- Model selection uses cross-validation on the training set. The final selected Logistic Regression model achieved a lapsed-class test F1 of `0.724`, above the required minimum of `0.55`.
- The retention list contains the top 10 highest-scored Premium customers within the test set. In this dataset, 2 of those 10 customers were actually lapsed.

### Limitations and Next Steps

The data is synthetic, so model performance and segment behaviour may not reflect real customer behaviour. Model probabilities are estimates, not guarantees. The Premium flag is based on whole-window RFM segmentation, which includes the September period used to define lapse. Therefore, the retention list is illustrative and is not a leakage-free evaluation of retention performance. The model's predictive features themselves use only pre-cutoff data.