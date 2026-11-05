import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag import retrieve

DB_PATH = "data/instamart.db"
LEDGER_PATH = "outputs/refund_ledger.jsonl"


# ---------------------------------------------------------------------
# Task 5: the five tools
# ---------------------------------------------------------------------
def get_order(order_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT order_id, status, order_amount, delivery_minutes FROM orders WHERE order_id = ?",
        (order_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return {"error": "order not found"}
    return {"order_id": row[0], "status": row[1],
            "order_amount": row[2], "delivery_minutes": row[3]}


def search_policy(query):
    return {"results": retrieve(query)}


def calculate_refund(order_amount, delivery_minutes):
    # Refund policy: delivered in MORE than 45 minutes -> full refund of the order amount.
    if delivery_minutes is None or delivery_minutes <= 45:
        return {"refund_inr": 0.0}
    return {"refund_inr": round(float(order_amount), 2)}


def _write_ledger(tool_name, order_id, refund_inr):
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(),
             "tool": tool_name, "order_id": order_id, "refund_inr": refund_inr}
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return {"refund_inr": refund_inr}


def issue_refund(order_id, refund_inr):
    return _write_ledger("issue_refund", order_id, refund_inr)


def escalate_to_human(order_id, refund_inr):
    return _write_ledger("escalate_to_human", order_id, refund_inr)


TOOLS_SPEC = [
    {"name": "get_order",
     "description": "Look up an order in the database by its order id.",
     "parameters": {"type": "object",
                    "properties": {"order_id": {"type": "string", "description": "e.g. ORD-100048"}},
                    "required": ["order_id"]}},
    {"name": "search_policy",
     "description": "Search the company policy documents and return the best matching passages.",
     "parameters": {"type": "object",
                    "properties": {"query": {"type": "string", "description": "what to look up"}},
                    "required": ["query"]}},
    {"name": "calculate_refund",
     "description": "Compute the refund in INR from the order amount and the delivery time in minutes.",
     "parameters": {"type": "object",
                    "properties": {"order_amount": {"type": "number"},
                                   "delivery_minutes": {"type": "number"}},
                    "required": ["order_amount", "delivery_minutes"]}},
    {"name": "issue_refund",
     "description": "Issue a refund of up to INR 1000 and record it in the refund ledger.",
     "parameters": {"type": "object",
                    "properties": {"order_id": {"type": "string"},
                                   "refund_inr": {"type": "number"}},
                    "required": ["order_id", "refund_inr"]}},
    {"name": "escalate_to_human",
     "description": "Send a refund above INR 1000 to a human support lead and record it in the ledger.",
     "parameters": {"type": "object",
                    "properties": {"order_id": {"type": "string"},
                                   "refund_inr": {"type": "number"}},
                    "required": ["order_id", "refund_inr"]}},
]

TOOL_MAP = {
    "get_order": get_order,
    "search_policy": search_policy,
    "calculate_refund": calculate_refund,
    "issue_refund": issue_refund,
    "escalate_to_human": escalate_to_human,
}


if __name__ == "__main__":
    print([t["name"] for t in TOOLS_SPEC])
    print(sorted(TOOL_MAP) == sorted(t["name"] for t in TOOLS_SPEC))
    print(TOOL_MAP["get_order"](**{"order_id": "ORD-100048"}))
    print(TOOL_MAP["get_order"](**{"order_id": "ORD-999999"}))
    print(TOOL_MAP["calculate_refund"](**{"order_amount": 128.25, "delivery_minutes": 65}))
    print(TOOL_MAP["calculate_refund"](**{"order_amount": 109.65, "delivery_minutes": 20}))
    print(TOOL_MAP["search_policy"](**{"query": "refund policy late delivery"})["results"][0]["source"])
