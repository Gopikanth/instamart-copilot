# Instamart Customer Intelligence Copilot

## Overview

This project builds a data and AI "Copilot" for Instamart, a quick-commerce grocery delivery company. Part A cleans messy customer, product and order exports, stores them in SQLite and analyses them with SQL and pandas. Part B segments customers and predicts who will lapse. Part C triages support tickets with an LLM and guardrails. Part D answers policy questions with retrieval and runs a refund agent. All amounts are in INR, and every result can be reproduced with the commands below.

## Reproduce

1. `python -m venv venv`
2. `source venv/bin/activate` (Windows: `venv\Scripts\activate`)
3. `pip install -r requirements.txt`
4. `python generate_data.py`
5. `python src/clean.py`
6. `python src/store.py`
7. `python src/validate.py`
8. `python src/run_queries.py`
9. `python src/analysis.py`

Commands for Parts B, C and D will be added as those parts are completed.

## Part A

To be completed.

## Part B

To be completed.

## Part C

To be completed.

## Part D

To be completed.

## Limitations and Next Steps

To be completed.