import json
import os

COUNTER_FILE = "data/counter.json"

def load_counters():
    if not os.path.exists(COUNTER_FILE):
        return {"calculations_total": 0, "calculations_with_contacts": 0}
    with open(COUNTER_FILE, "r") as f:
        return json.load(f)

def save_counters(data):
    with open(COUNTER_FILE, "w") as f:
        json.dump(data, f)

def increment_calculation():
    counters = load_counters()
    counters["calculations_total"] += 1
    save_counters(counters)
    return counters["calculations_total"]

def increment_lead():
    counters = load_counters()
    counters["calculations_with_contacts"] += 1
    save_counters(counters)
    return counters["calculations_with_contacts"]