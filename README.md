Instamart Customer Intelligence Copilot
Overview

This project builds a data and AI "Copilot" for Instamart, a quick-commerce grocery delivery company. Part A cleans messy customer, product and order exports, stores them in SQLite and analyses them with SQL and pandas. Part B segments customers and predicts who will lapse. Part C triages support tickets with an LLM and guardrails. Part D answers policy questions with retrieval and runs a refund agent. All amounts are in INR, and every result can be reproduced with the commands below.

Reproduce
python -m venv venv
source venv/bin/activate (Windows: venv\Scripts\activate)
pip install -r requirements.txt
python generate_data.py
python src/clean.py
python src/store.py
python src/validate.py
python src/run_queries.py
python src/analysis.py

Commands for Parts B, C and D will be added as those parts are completed.

Part A

Part A turns the raw exports in data/raw/ into clean tables, stores them in SQLite, and analyses them with SQL and pandas.

Step	Script	Output
Clean	src/clean.py	data/clean/customers.csv, data/clean/products.csv, data/clean/orders.csv
Store	src/store.py	data/instamart.db (tables customers, products, orders)
Validate	src/validate.py	prints ALL CHECKPOINTS PASSED
SQL	src/run_queries.py and sql/queries.sql	Q1 to Q7
pandas	src/analysis.py	pivot table, city summary, statistics, correlations
Data cleaning

Raw files are never modified. Cleaning is done in src/clean.py and the results are saved to data/clean/.

Customers (1,200 rows)

Rule	Values changed
City: strip spaces and apply title case (24 spellings become 6 cities)	476
Gender: lowercase and map m/f/male/female to male or female	920
Gender: blank values set to unknown	30
Age: values outside 10 to 100 set to missing	6
Age: missing values (61 blank plus 6 out of range) filled with the median age of the customer's city	67
signup_date converted to a datetime	1,200

Orders (13,084 raw rows)

Order	Rule	Rows or values changed
1	order_ts converted to a datetime	13,084
2	Exact duplicate rows removed (13,084 to 12,965 rows)	119
3	Only the latest record kept per order_id after sorting by order_ts (12,965 to 12,309 rows)	656
4	order_amount converted to numeric; unreadable entries set to missing, then filled with round(price_inr x quantity x (1 - discount_pct / 100), 2)	112
5a	Negative delivery_minutes set to missing	105
5b	Missing delivery_minutes of completed orders filled with the median of the product category among completed orders (669 originally blank plus the 105 negatives)	774
5c	Missing delivery_minutes of cancelled orders left blank on purpose	1,199 kept blank

Note on rule 4: the raw file had 120 unreadable amounts. Eight of them were on duplicate or superseded rows that were removed in rules 2 and 3, so 112 remained to be filled.

Cleaned data summary
Table	Rows
customers	1,200
products	40
orders	12,309
Order status	Count
completed	11,110
cancelled	1,199
pending	0

Sum of order_amount over completed orders: INR 2,998,668.80.

Validation

src/validate.py reads the SQLite database and asserts eight checkpoints: 12,309 orders, 1,200 customers, 11,110 completed orders, 1,199 cancelled orders, 0 pending orders, 0 missing order_amount, a completed-order total of INR 2,998,668.80, and 1,199 cancelled orders with a blank delivery_minutes. It prints ALL CHECKPOINTS PASSED.

SQL queries

All seven queries are in sql/queries.sql and run with python src/run_queries.py.

Query	Technique	Result
Q1	WHERE and HAVING: customers with more than INR 8,000 in completed orders above INR 500	30 customers; top is C0693 with 6 orders and INR 13,776.55
Q2	Three-table join: revenue by city and product category (completed orders)	30 rows; largest is Bengaluru / Electronics at INR 233,909.45; the 30 revenues sum to INR 2,998,668.80
Q3	Scalar subquery: products priced above the average price (INR 289.325)	11 products; most expensive is P038 Bluetooth Speaker at INR 1,999
Q4	LEFT JOIN: customers with no completed order	25 customers (18 never ordered, 7 only have cancelled orders); first is C0029 from Hyderabad
Q5	CTE: customers whose total spend is above the average customer total (INR 2,552.06)	550 customers; top is C0693 at INR 14,766.55
Q6	Window functions: RANK, DENSE_RANK and ROW_NUMBER per city	1,175 customers; 8 rows have RANK different from ROW_NUMBER
Q7	Running total: daily completed revenue	183 days from 2025-04-01 to 2025-09-30; final cumulative revenue INR 2,998,668.80

Top customer per city in Q6:

City	Customer	Total spend (INR)
Bengaluru	C0082	12,856.20
Chennai	C0930	10,151.40
Delhi	C0291	13,742.60
Hyderabad	C0743	12,730.05
Mumbai	C0693	14,766.55
Pune	C0426	10,377.10

Why ties make RANK differ from ROW_NUMBER: when two customers in the same city have exactly the same total spend, RANK gives them the same rank (and skips the next number), while ROW_NUMBER always gives every row a different number.

pandas cross-check

The analysis in src/analysis.py uses completed orders joined to customers (for city) and products (for category), 11,110 rows.

A pivot table of order_amount (sum) by city and category has a grand total of INR 2,998,668.80, the same as the SQL result. The Bengaluru / Electronics cell is INR 233,909.45, the same as Q2.

City	Total (INR)	Mean order (INR)	Orders
Bengaluru	523,643.40	276.47	1,894
Chennai	463,629.15	272.72	1,700
Delhi	502,829.80	243.62	2,064
Hyderabad	528,589.90	284.95	1,855
Mumbai	479,058.50	297.00	1,613
Pune	500,918.05	252.48	1,984
Statistics and outliers (completed order_amount)
Statistic	Value
Mean	INR 269.91
Median	INR 135.00
Skewness	4.61
Q1 / Q3	INR 64.80 / INR 297.00
IQR	INR 232.20
Lower fence / upper fence (1.5 x IQR)	INR -283.50 / INR 645.30
Outliers below / above the fences	0 / 897

Correlation matrix (completed orders):

	order_amount	discount_pct	quantity	delivery_minutes
order_amount	1.000	-0.095	0.087	-0.003
discount_pct	-0.095	1.000	-0.000	-0.010
quantity	0.087	-0.000	1.000	-0.013
delivery_minutes	-0.003	-0.010	-0.013	1.000

The strongest relationship in absolute value is between order_amount and discount_pct at about -0.095.

Interpretation

This data records Instamart quick-commerce orders: 1,200 customers in six Indian cities buying 40 products across five categories between April and September 2025, with 11,110 completed orders worth INR 2,998,668.80.

Order amounts are strongly right-skewed. The mean (INR 269.91) is about double the median (INR 135.00), with skewness of 4.61, Q1 of 64.80 and Q3 of 297.00.

Using the 1.5xIQR rule, the upper fence is INR 645.30 and 897 orders lie above it; none fall below the lower fence. About 70% of these are Electronics purchases, so they look like genuine expensive orders, not data errors, and I kept them.

Correlations are weak. The largest in absolute value is order_amount with discount_pct (about -0.095), followed by order_amount with quantity (+0.087); delivery_minutes is essentially unrelated to everything else. Correlation of this size does not establish causation.

Part B

To be completed.

Part C

To be completed.

Part D

To be completed.

Limitations and Next Steps

To be completed.