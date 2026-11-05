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

Part B groups customers into segments and predicts which customers will lapse. It uses only completed orders for customer behaviour and reads data/clean/orders.csv and data/clean/customers.csv from Part A.

Script	What it does	Output
src/rfm.py	RFM table, K-means, segment profile, PCA	outputs/customer_segments.csv
src/lapse_data.py	Cohort, label, features, split, preprocessing (imported by the next script)	none
src/lapse_model.py	Tuning, evaluation, class-balance experiment, interpretation, saved model, retention list	outputs/lapse_model.joblib, outputs/retention_list.csv
Leakage controls
No encoder, scaler or resampler saw test rows. Encoding and scaling are fitted inside a pipeline on training data only, and the oversampling is applied to the training set only.
No data from 2025-09-01 onwards entered the features.
The segment labels from the K-means task were not used as features.
Customer segments

RFM per customer, from completed orders and a snapshot date of 2025-10-01: recency is the days since the last completed order, frequency is the number of distinct completed orders, and monetary is the sum of order_amount. There are 1,175 customers with at least one completed order. The three columns were scaled with StandardScaler, and K-means used n_init=10 and random_state=42.

K	Inertia	Silhouette
2	1820.8	0.465
3	1268.2	0.445
4	743.1	0.526
5	617.4	0.480
6	503.2	0.482
7	408.5	0.416
8	366.5	0.412

I chose K = 4: the silhouette is highest there (0.526), the inertia curve has its elbow between K = 3 and K = 4, and four segments are few enough for a retention team to act on. Inertia always falls as K grows (K = 1,175 would give every customer their own cluster and an inertia of 0), so inertia alone cannot choose K.

Segment	Name	Size	Mean recency (days)	Mean frequency	Mean monetary (INR)	Recommended action
0	Casual Buyers	436	28.9	3.8	1,057.6	Nudge a second and third order with a small welcome offer
1	Premium Big Spenders	138	24.1	6.8	7,129.7	Priority service, early access to new Electronics and loyalty perks
2	Loyal Regulars	419	8.8	19.4	3,410.0	Keep them engaged with subscriptions and referral rewards
3	Lapsing Customers	182	109.0	2.2	686.0	Win-back campaign with a discount

Cluster numbers are only labels and carry no ordering. The Premium flag marks the segment with the highest mean monetary value (the 138-customer segment).

PCA with two components on the scaled RFM matrix explains 0.634 and 0.218 of the variance, 0.852 in total, so a 2D view keeps about 85% of the information. The segments are saved in outputs/customer_segments.csv with the columns customer_id, recency, frequency, monetary, segment_id, segment_name and is_premium.

Lapse prediction

Problem definition. The cutoff is 2025-09-01. The cohort is every customer with at least one completed order before the cutoff: 1,156 customers. The label lapsed is 1 if the customer has no completed order from 2025-09-01 to 2025-09-30, and 0 otherwise: 443 customers lapsed (38.32%).

Features (all from orders before the cutoff): recency, frequency, monetary, average discount, average delivery minutes, favourite category, cancellation rate, city, age, gender and tenure in days. There are no missing values in the features.

Split. An 80/20 stratified split with random_state=42 gives 924 training and 232 test customers. The baseline that always predicts "not lapsed" has an accuracy of 0.616 and an F1 of 0.0 on the lapsed class, so it finds none of the customers who lapse.

Preprocessing. One-hot encoding with drop="first" for city, gender and favourite category, and standard scaling for the numeric columns, fitted on the training rows only (19 columns after encoding). As a check, the learned mean of frequency is 8.116, from the 924 training rows, while the mean over all 1,156 cohort customers is 8.029. They differ because they are averages of different customers, which shows that the scaler never saw the test rows.

Tuning and evaluation

Both searches use 5-fold cross-validation with F1 on the lapsed class, and the preprocessing sits inside the pipeline, so it is refitted in every fold.

Model	Grid	Best parameters	Best cross-validated F1
Logistic regression (max_iter=1000)	C in 0.01, 0.1, 1, 10, 100	C = 0.1	0.639
Random forest (n_estimators=100, random_state=42)	max_depth in 3, 5, 8 and min_samples_leaf in 5, 10, 20	max_depth = 3, min_samples_leaf = 20	0.669

Results on the untouched test set (lapsed class), evaluated once after tuning:

Model	Confusion matrix [[TN, FP], [FN, TP]]	Precision	Recall	F1
Baseline (always "not lapsed")	n/a	0.000	0.000	0.000
Logistic regression	[[105, 38], [17, 72]]	0.655	0.809	0.724
Random forest	[[112, 31], [21, 68]]	0.687	0.764	0.723

My numbers differ from the reference values in the brief (best C = 1, depth 8 and leaf 10) because my feature set is different, but they are of the same order and well above the required test F1 of 0.55.

Model choice

I select the logistic regression. Both tuned models reach almost the same test F1 (about 0.72), but logistic regression catches more of the customers who really lapse (recall 0.81 versus 0.76). Missing a customer who is about to lapse loses all their future revenue, while wrongly targeting a loyal customer only wastes a small discount, so recall is worth more than a few points of precision. Logistic regression is also simpler to explain to the retention team through its coefficients.

Class-balance experiment

The training set has 570 customers who did not lapse and 354 who did. I kept every original training row and added 216 randomly chosen duplicates of lapsed training rows (with replacement, random_state=42), giving 570 of each class (1,140 rows). I refitted the best logistic regression on this balanced set and evaluated on the original test set.

Model	Precision	Recall	F1	Confusion matrix
Original logistic regression	0.655	0.809	0.724	[[105, 38], [17, 72]]
Balanced logistic regression	0.587	0.910	0.714	[[86, 57], [8, 81]]

Recall moved the most, from 0.81 to 0.91, while precision fell from 0.66 to 0.59 and F1 stayed about the same. For the retention team, balancing means catching more of the customers who are about to lapse (81 of 89 instead of 72), at the cost of contacting more loyal customers by mistake (57 instead of 38). That is worth it when a retention offer is cheap compared with the value of a lost customer.

Interpretation

Five most important features of the best random forest:

Feature	Importance	Business reading
frequency	0.350	How often someone orders is the strongest signal; habit decides who stays
monetary	0.243	Total spend before September matters; big spenders behave differently
recency	0.108	Days since the last order, the classic early-warning sign
cancel_rate	0.068	Customers who often cancel have a worse experience
avg_discount	0.065	How much a customer relies on promotions

Signs of three coefficients in the best logistic regression (the category baseline is Dairy):

Feature	Coefficient	Sign	Business reading
frequency	-1.281	negative	More orders means a lower chance of lapsing; by far the biggest effect
fav_category_Electronics	-0.378	negative	Electronics buyers lapse less than Dairy buyers
cancel_rate	-0.101	negative	A weak and slightly surprising sign: more cancellations do not predict lapsing here, so I would not act on it
Saved model and retention list

The selected logistic regression pipeline is saved with joblib.dump to outputs/lapse_model.joblib. Reloading it with joblib.load reproduces the original test predictions exactly (all predictions identical).

There are 29 Premium customers in the test set. The top 10 by predicted lapse probability are saved in outputs/retention_list.csv (columns customer_id, lapse_probability, actually_lapsed). Of these 10, 2 truly lapsed.

customer_id	lapse_probability	actually_lapsed
C0577	0.5750	0
C0102	0.5704	1
C0697	0.5475	0
C0942	0.5099	0
C0831	0.4959	0
C0509	0.4765	0
C0162	0.4764	0
C0324	0.4763	0
C0977	0.4449	1
C0299	0.4447	0

The retention list is illustrative and not a leakage-free evaluation, because the Premium flag comes from RFM over the whole window, which includes the September period that defines the lapse label.


Part C

Part C builds a triage pipeline around the supplied offline mock_llm.py for 164 support tickets. It is safe (input guardrails and redaction), resilient (retries with backoff), checked (every answer is validated), cost-aware (token budget) and useful (routing that uses the Part B segments). Tickets are processed in file order. Everything runs with python src/triage.py, which reads data/raw/tickets.csv and outputs/customer_segments.csv and writes outputs/triage_budget_demo.csv and outputs/triage_results.csv.

Input guardrails

Before any model call, a ticket whose text is empty or only whitespace gets the status skipped_empty, and a ticket whose estimated size is above MAX_INPUT_TOKENS = 400 gets flagged_long. Neither is ever sent to the model. There are 4 empty tickets and 4 long tickets (each estimated at 734 tokens), which leaves 156 eligible tickets. The file is read with keep_default_na=False, so an empty cell stays an empty string.

Redaction

The three patterns are applied in this order to the ticket text before it goes into a prompt: email to [EMAIL], phone (\b[6-9]\d{9}\b) to [PHONE] and order id (ORD-\d{6}) to [ORDER_ID].

Type	Substitutions across all 164 tickets
Emails	55
Phone numbers	91
Order ids	132
Total	278

Re-applying the three patterns to the redacted texts finds 0 matches (checked with an assertion). The user message sent to the model is exactly the redacted ticket text, and an assertion before every call checks that no email, phone number or order id appears in any message of the prompt.

Prompts

Both prompts contain the word CLASSIFY, list the four categories and require a JSON-only reply. The few-shot prompt adds a line EXAMPLES: followed by four labelled examples (billing, delivery, technical and fraud).

Zero-shot (26 estimated tokens):
CLASSIFY the support ticket into one category: billing, delivery, technical or fraud. Reply with JSON only: {"category": "...", "reason": "..."}

Few-shot (98 estimated tokens): the zero-shot text plus
EXAMPLES:
Ticket: I was charged twice for one order. -> {"category": "billing", "reason": "double charge"}
Ticket: The rider has not arrived yet. -> {"category": "delivery", "reason": "late rider"}
Ticket: The app crashes when I log in. -> {"category": "technical", "reason": "app crash"}
Ticket: Someone used my card without permission. -> {"category": "fraud", "reason": "unauthorized use"}
Resilient calls

Every model call goes through a retry function with at most 3 retries per ticket. The wait before retry number n is BASE_DELAY * 2**n * random.uniform(0.9, 1.15) with BASE_DELAY = 0.05 seconds, and one log line is printed per retry with the ticket id, the retry number and the wait. mock_llm.reset() is called immediately before each full run. A full run over the 156 eligible tickets produces 19 TransientLLMErrors; all 19 were recovered by a retry, and no ticket ended with a permanent error. With this mock every retry is retry number 0, and the 19 waits lie between 0.0453 and 0.0562 seconds, inside the allowed range of 0.045 to 0.0575.

Output validation

A reply is parsed as JSON and accepted if category is one of the four allowed values (classified_json). If it is not valid JSON, the lowercase words are extracted with re.findall(r"[a-z]+", text.lower()) and the reply is accepted if exactly one allowed category word is present (classified_keyword). In every other case, including valid JSON with a category outside the list, the status is flagged_invalid_output and the ticket goes to human review. Nothing is guessed. The extraction uses re.findall rather than a whitespace split, because billing-related must give the words billing and related; a plain split would give 135 / 0 / 21 instead of 135 / 12 / 9.

Status (one full run over 164 tickets)	Count
classified_json	135
classified_keyword	12
flagged_invalid_output	9
skipped_empty	4
flagged_long	4

The 12 keyword replies are the mock's chatty answers (for example "The customer appears to have a billing-related problem."), and the 9 invalid ones are valid JSON with the category shipping.

Zero-shot versus few-shot

Each prompt was run once over all tickets with no token budget. Accuracy is measured against true_category over the 147 classified tickets.

	Zero-shot	Few-shot
Tickets classified	147	147
Accuracy	85.7% (126 of 147)	100% (147 of 147)
Total tokens	8,464	19,696
Tokens per classified ticket	57.6	134.0

Zero-shot confusion table (rows are the true category, columns the predicted category):

true \ predicted	billing	delivery	fraud	technical
billing	38	0	0	0
delivery	0	36	0	0
fraud	11	0	23	0
technical	10	0	0	29

Few-shot raised accuracy from 85.7% to 100% (126 to 147 of 147 classified tickets correct), but it cost 19,696 tokens instead of 8,464, which is 134 versus 58 tokens per classified ticket (about 2.3 times as much). All 21 zero-shot errors were fraud (11) or technical (10) tickets labelled billing, and a missed fraud ticket is the costly kind of mistake. So for this task the extra 76 tokens per ticket (about 535 tokens for each additional correct ticket) is worth paying. For a low-risk, high-volume task where 86% accuracy is acceptable, the cheaper zero-shot prompt would be enough.

Token budget

TOKEN_BUDGET works like this: before each model call, if the running total of usage.total_tokens is already at or above the budget, no call is made and the ticket gets the status budget_exhausted and goes to human review. The demo uses the zero-shot prompt with TOKEN_BUDGET = 6000 and is saved as outputs/triage_budget_demo.csv. The run used 6,027 tokens (slightly above the budget, because the check happens before each call) and 45 tickets ended as budget_exhausted. The count depends on the prompt length.

Routing and final output

The final outputs/triage_results.csv (164 rows; columns ticket_id, customer_id, status, category, segment_name, priority, route, tokens_used) comes from a few-shot run with TOKEN_BUDGET = 100000. It uses outputs/customer_segments.csv from Part B for the Premium flag; a customer with no row in that file counts as not premium.

Rule, in this order	Route	Priority
Status is skipped_empty, flagged_long, flagged_invalid_output or budget_exhausted	human_review	NORMAL
Category is fraud	security_team	HIGH
Customer is Premium	premium_desk	HIGH
Otherwise	support_queue	NORMAL
Route	Tickets
support_queue	102
security_team	34
human_review	17
premium_desk	11

Rule-validated and human-reviewed. 147 tickets (135 classified_json and 12 classified_keyword) were classified and passed the validation rules, and were routed automatically. 17 tickets went to humans: 4 empty, 4 too long and 9 whose output could not be validated. In the budget demo, 45 further tickets would have gone to humans because the budget ran out.


Part D

To be completed.

Limitations and Next Steps

The retention list is illustrative and not a leakage-free evaluation. The Premium flag is a post-hoc whole-window label computed from RFM over all orders, including the September window that defines the lapse label. The model's own features use only orders before the cutoff.
The lapse model is trained and tested on a small cohort (1,156 customers, 232 in the test set, 29 Premium customers), with a single cutoff date, so the metrics are noisy.
The mock model is deterministic and keyword-based, so the zero-shot and few-shot accuracies say little about how a real LLM would behave. The few-shot result of 100% reflects how the mock treats the EXAMPLES: marker.
Redaction only covers the three required patterns (email, phone, order id). Names, addresses and card numbers in free text would not be removed.
Long tickets are flagged for a human and not truncated or summarised, and token counts are estimates (words x 1.3), not real billing tokens.