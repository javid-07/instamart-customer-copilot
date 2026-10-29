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

**Objective:** Analyse customer purchasing behaviour using Recency, Frequency, and Monetary (RFM) metrics.

**Methodology:**
- Used `2025-10-01` as the snapshot date.
- Considered completed orders for RFM calculations.
- Recency measures the number of days since the latest completed order.
- Frequency measures the number of unique completed orders per customer.
- Monetary represents the total order amount from completed orders.
- Aggregated the metrics at customer level.

**Results:**

| Metric | Value |
|---|---:|
| Customers analysed | 1,175 |
| Median recency | 19 days |
| Minimum recency | 0 days |
| Maximum recency | 180 days |
| Average frequency | 9.46 orders |
| Maximum frequency | 33 orders |
| Average monetary value | ₹2,552.06 |
| Maximum monetary value | ₹14,766.55 |

**Output:** `outputs/rfm.csv`

**Reproduce:**

```bash
python src/build_rfm.py
```

### Task 2: K-Means Clustering

**Objective:** Group customers with similar purchasing behaviour using K-Means clustering.

**Methodology:**
- Used Recency, Frequency, and Monetary as clustering features.
- Standardised the features using `StandardScaler`.
- Evaluated K values from 2 to 8.
- Used `n_init=10` and `random_state=42`.
- Compared inertia and silhouette scores to assess clustering quality.

**Results:**

| K | Inertia | Silhouette Score |
|---:|---:|---:|
| 2 | 1820.8 | 0.465 |
| 3 | 1268.2 | 0.445 |
| 4 | 743.1 | 0.526 |
| 5 | 617.4 | 0.480 |
| 6 | 503.2 | 0.482 |
| 7 | 408.5 | 0.416 |
| 8 | 366.5 | 0.412 |

K=4 was selected because it achieved the highest silhouette score among the tested values. Inertia decreases as K increases, so inertia alone was not used to select the final cluster count.

**Output:** `outputs/kmeans_evaluation.csv`

**Reproduce:**

```bash
python src/cluster_customers.py
```

### Task 3: Segment Profiling and Premium Identification

**Objective:** Describe customer segments and identify the segment with the highest mean monetary value.

**Methodology:**
- Applied K-Means with K=4 using standardised RFM features.
- Used `random_state=42` and `n_init=10`.
- Calculated segment sizes and average RFM metrics.
- Used PCA to evaluate how much variance the first two principal components explain.
- Assigned descriptive segment names based on customer profiles.
- Set the Premium flag for customers belonging to the segment with the highest mean monetary value.

**Segment profiles:**

| Segment ID | Segment Name | Customers | Mean Recency (days) | Mean Frequency | Mean Monetary (₹) |
|---:|---|---:|---:|---:|---:|
| 0 | Occasional Shoppers | 436 | 28.86 | 3.77 | 1,057.62 |
| 1 | Premium Spenders | 138 | 24.12 | 6.77 | 7,129.70 |
| 2 | Loyal Frequent Buyers | 419 | 8.77 | 19.40 | 3,410.02 |
| 3 | At-Risk Inactive Customers | 182 | 109.04 | 2.20 | 685.99 |

Cluster IDs are arbitrary labels; their numeric order does not represent customer value or loyalty.

**PCA results:**
- First principal component explained variance: 0.634.
- Second principal component explained variance: 0.218.
- Combined explained variance: 0.852 (85.2%).

**Business interpretation:**
- **Occasional Shoppers:** Encourage repeat purchases through relevant offers.
- **Premium Spenders:** Prioritise personalised rewards and retention campaigns.
- **Loyal Frequent Buyers:** Support continued engagement with loyalty benefits.
- **At-Risk Inactive Customers:** Consider targeted reactivation campaigns.

These are proposed actions based on the segment profiles; campaign effectiveness has not been measured.

**Output:** `outputs/customer_segments.csv`

The file contains `customer_id`, `recency`, `frequency`, `monetary`, `segment_id`, `segment_name`, and `is_premium`.

The Premium flag is true for exactly 138 customers in Segment 1, which has the highest mean monetary value.

**Reproduce:**

```bash
python src/save_segments.py
```

### Task 4: Lapse Cohort and Label Construction

**Objective:** Identify customers who became lapsed during the observation period.

**Methodology:**
- Used completed orders before `2025-09-01` to define the eligible customer cohort.
- Defined the observation period as `2025-09-01` through `2025-09-30`.
- Labelled a customer as lapsed if they had no completed order during the observation period.
- Labelled a customer as non-lapsed if they had at least one completed order during the period.

**Results:**

| Metric | Value |
|---|---:|
| Eligible customers | 1,156 |
| Lapsed customers | 443 |
| Non-lapsed customers | 713 |
| Lapse rate | 38.32% |
| Training rows | 924 |
| Test rows | 232 |

The train/test split is stratified to preserve the target-class distribution.

**Reproduce:**

```bash
python src/build_lapse_dataset.py
```

### Task 5: Lapse Prediction Feature Engineering

**Objective:** Create a customer-level feature dataset for lapse prediction while preventing future-data leakage.

**Methodology:**
- Restricted order-derived predictive features to orders strictly before `2025-09-01`.
- Created historical purchasing features including recency, frequency, monetary value, average discount percentage, and average delivery time.
- Calculated cancellation rate from historical order statuses.
- Derived favourite category from completed historical orders.
- Included customer attributes such as city, age, gender, and tenure.
- Kept the target label separate from the model input features.
- Checked for duplicate customer IDs and missing feature values.

**Validation results:**
- Duplicate customer IDs: 0.
- Missing feature values: 0.
- Negative tenure values: 0.
- Minimum tenure: 154 days.
- Maximum tenure: 609 days.

**Leakage prevention:**
- No order data dated `2025-09-01` or later was used to construct predictive features.
- Segment IDs and segment names from Task 3 were not used as predictive features.
- Scaling and categorical encoding were fitted using training data only, through the model pipeline.
- The training scaler's frequency mean was 8.1158, while the full-cohort frequency mean was 8.0285. This difference is expected because the scaler was fitted on the training subset.

**Reproduce:**

```bash
python src/build_lapse_features.py
```

### Task 6: Baseline Evaluation

**Objective:** Establish a baseline for evaluating lapse prediction models.

**Methodology:**
- Split the data into 924 training rows and 232 test rows.
- Used stratified splitting with `random_state=42`.
- Created a majority-class baseline that predicts every customer as non-lapsed.
- Evaluated accuracy, lapsed-class F1-score, and the confusion matrix.
- Verified that preprocessing transformations were fitted on training data and then applied to test data.

**Results:**

| Metric | Baseline |
|---|---:|
| Test rows | 232 |
| Accuracy | 0.616 |
| Lapsed-class F1-score | 0.000 |
| True negatives | 143 |
| False positives | 0 |
| False negatives | 89 |
| True positives | 0 |

Confusion matrix order: `[[TN, FP], [FN, TP]]`.

The baseline does not identify any lapsed customers. Although it achieves 0.616 accuracy, its lapsed-class F1-score is zero, making it unsuitable for a retention workflow.

**Preprocessing verification:**

| Check | Result |
|---|---:|
| Transformed training shape | 924 × 19 |
| Transformed test shape | 232 × 19 |
| Training scaler frequency mean | 8.1158 |
| Full-cohort frequency mean | 8.0285 |
| Missing feature values | 0 |

**Output:** `outputs/lapse_features.csv`

**Reproduce:**

```bash
python src/train_lapse_model.py
```

### Task 7: Model Tuning and Comparison

**Objective:** Tune Logistic Regression and Random Forest and compare their lapse prediction performance.

**Methodology:**
- Used five-fold cross-validation with F1-score as the tuning metric.
- Logistic Regression grid: `C = [0.01, 0.1, 1, 10, 100]`.
- Random Forest grid: `max_depth = [3, 5, 8]`, `min_samples_leaf = [5, 10, 20]`, and `n_estimators=100`.
- Used `random_state=42` for Random Forest.
- Applied `StandardScaler` to numeric features and `OneHotEncoder(drop="first", handle_unknown="ignore")` to categorical features.
- Evaluated precision, recall, and F1-score for the lapsed (positive) class.

**Results:**

| Metric | Logistic Regression | Random Forest |
|---|---:|---:|
| Best cross-validation F1 | 0.639 | 0.672 |
| Test accuracy | 0.763 | 0.763 |
| Lapsed-class precision | 0.65 | 0.67 |
| Lapsed-class recall | 0.81 | 0.74 |
| Lapsed-class F1-score | 0.724 | 0.706 |

Logistic Regression was selected because it achieved the higher held-out test F1-score of 0.724, exceeding the required minimum of 0.55.

**Feature Importance — Random Forest**

The five most important features identified by the Random Forest model are:

| Feature | Importance | Business Interpretation |
|---|---:|---|
| Frequency | 0.400839 | Historical purchase frequency is the strongest feature for distinguishing lapsed customers. |
| Monetary | 0.257073 | Total historical spending contributes substantially to lapse prediction. |
| Recency | 0.088255 | Time since the last completed order provides additional information about customer inactivity. |
| Cancellation Rate | 0.082872 | Customers' historical cancellation behaviour helps the model distinguish purchasing patterns. |
| Average Discount Percentage | 0.054833 | Historical discount usage contributes to predicting lapse risk. |

**Logistic Regression — Coefficient Interpretation**

The following are the three largest coefficients by absolute magnitude among the reported coefficients:

| Feature | Coefficient | Interpretation |
|---|---:|---|
| Frequency | -1.281146 | Higher historical purchase frequency is associated with lower predicted lapse odds, holding other features constant. |
| Favourite Category: Electronics | -0.378188 | This encoded category is associated with lower predicted lapse odds relative to the reference category, holding other features constant. |
| Favourite Category: Snacks | -0.202604 | This encoded category is associated with lower predicted lapse odds relative to the reference category, holding other features constant. |

The negative coefficients indicate lower predicted log-odds of lapse, conditional on the other model features. These are model associations, not evidence of causation.

**Reproduce:**

```bash
python src/tune_lapse_models.py
```

### Task 8: Class-Balance Experiment

**Objective:** Evaluate the effect of class balancing on lapse prediction.

**Results:**

| Metric | Original Training Data | Balanced Experiment |
|---|---:|---:|
| Lapsed-class precision | 0.655 | 0.587 |
| Lapsed-class recall | 0.809 | 0.910 |
| Lapsed-class F1-score | 0.724 | 0.714 |

The balanced experiment increased recall but reduced precision and F1-score. This shows a trade-off: more lapsed customers were identified, but the proportion of correctly identified customers decreased.

**Reproduce:**

```bash
python src/balance_experiment.py
```

### Task 9: Save and Validate the Final Model

**Objective:** Save the selected model pipeline and confirm that the saved model produces consistent predictions.

**Methodology:**
- Refit the selected model pipeline using the defined training procedure.
- Saved the fitted pipeline as a Joblib artifact.
- Reloaded the saved model and compared its predictions with those produced before saving.

**Results:**
- Saved model: `outputs/lapse_model.joblib`.
- Test F1-score: 0.724.
- Reloaded predictions matched the original predictions: True.

**Reproduce:**

```bash
python src/save_lapse_model.py
```

### Task 10: Retention List Generation

**Objective:** Create an illustrative list of Premium customers ranked by predicted lapse probability.

**Methodology:**
- Identified Premium customers in the held-out test set.
- Ranked customers by predicted lapse probability.
- Exported the top 10 customers for illustrative retention outreach.

**Results:**
- Premium customers in the test set: 29.
- Customers included in the retention list: 10.
- Customers among the top 10 who were actually labelled as lapsed: 2.

**Output:** `outputs/retention_list.csv`

The file contains `customer_id`, `lapse_probability`, and `actually_lapsed`.

**Reproduce:**

```bash
python src/create_retention_list.py
```

### Part B: Outputs Summary

| Output | Purpose |
|---|---|
| `outputs/rfm.csv` | Customer-level RFM metrics |
| `outputs/kmeans_evaluation.csv` | K-Means inertia and silhouette scores |
| `outputs/customer_segments.csv` | Segment assignments and Premium flags |
| `outputs/lapse_features.csv` | Model features and lapse labels |
| `outputs/lapse_model.joblib` | Saved lapse prediction pipeline |
| `outputs/retention_list.csv` | Ranked illustrative retention list |

### Part B: Limitations

- Segment names are descriptive interpretations of observed customer profiles and have not been independently validated.
- The Premium flag is derived from whole-window RFM segmentation, which includes activity from the September observation period. Therefore, the Premium-based retention list is illustrative and must not be treated as a leakage-free model evaluation.
- Predictive model features are restricted to information available before `2025-09-01`.
- The model metrics come from a single stratified hold-out split; performance may vary on other datasets or time periods.
- Retention recommendations have not been validated through a live campaign or controlled experiment.

## Part C: Support Ticket Triage with Guardrails

### Task 1: Input Guardrails

**Implementation:** `src/triage_tickets.py`

The input guardrail stage loads `data/raw/tickets.csv` and processes tickets in their original file order. Missing ticket text is treated as empty input.

- Empty or whitespace-only tickets are assigned `skipped_empty`.
- Tickets with estimated input tokens greater than `MAX_INPUT_TOKENS = 400` are assigned `flagged_long`.
- All remaining tickets are marked `eligible` for subsequent pipeline stages.
- The token estimate is calculated using `mock_llm.est_tokens()`.
- No model calls are made during this stage.

**Verified results:**

| Check | Result |
|---|---:|
| Total tickets | 164 |
| Empty tickets skipped | 4 |
| Long tickets flagged | 4 |
| Eligible tickets | 156 |
| Estimated tokens per long ticket | 734 |

The script includes assertions to verify the ticket count, original file order, and expected status counts.

**Reproduce:**

```powershell
python .\src\triage_tickets.py

### Task 2: PII Redaction

**Implementation:** `redact_pii()` in `src/triage_tickets.py`

Before ticket text is used by subsequent pipeline stages, the redaction
function applies the required regular expressions in this exact order:

1. Email addresses matching `[\w.+-]+@[\w-]+\.[\w.]+` are replaced with `[EMAIL]`.
2. Phone numbers matching `\b[6-9]\d{9}\b` are replaced with `[PHONE]`.
3. Order IDs matching `ORD-\d{6}` are replaced with `[ORDER_ID]`.

The implementation uses `re.subn()` to replace matches and count the
number of replacements. Redacted text and per-ticket redaction counts
are stored by `prepare_tickets()`.

**Verified redaction counts across all 164 tickets:**

| PII type | Replacement | Count |
|---|---|---:|
| Email addresses | `[EMAIL]` | 55 |
| Phone numbers | `[PHONE]` | 91 |
| Order IDs | `[ORDER_ID]` | 132 |
| **Total** | | **278** |

**Verification results:**
- All expected redaction counts matched.
- PII remaining in prepared ticket text: 0.
- The script prints redaction counts and asserts the expected totals.
- The user-message helper returns a message whose content contains only
  the supplied redacted ticket text.
- Task 1 guardrail counts remain correct: 4 empty, 4 long, 156 eligible.

**Reproduce:**

```powershell
python .\src\triage_tickets.py