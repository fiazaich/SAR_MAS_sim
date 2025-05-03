import os
import json
import csv
from collections import defaultdict
import matplotlib.pyplot as plt

# — Publication style —  
plt.style.use('seaborn-v0_8-paper')
plt.rc('font',      family='serif', size=10)
plt.rc('mathtext',  fontset='dejavuserif')
plt.rc('axes',      titlesize=16, labelsize=12, titleweight='semibold')
plt.rc('xtick',     labelsize=10)
plt.rc('ytick',     labelsize=10)

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))

def sanitize_log_file(path):
    with open(path, "r") as f:
        lines = f.readlines()

    # Fix header if it has tabs but data is comma-separated
    if "\t" in lines[0] and "," in lines[1]:
        lines[0] = lines[0].replace("\t", ",")
        with open(path, "w") as f:
            f.writelines(lines)


def evaluate_semantic_coherence(log_dir=BASE):
    import os
    import json
    import csv

    ontology_path = os.path.join(log_dir, "ontology_access.json")
    log_path = os.path.join(log_dir, "update_log.csv")

    if not os.path.exists(ontology_path):
        raise FileNotFoundError("ontology_access.json not found in logs folder")
    if not os.path.exists(log_path):
        raise FileNotFoundError("update_log.csv not found in logs folder")

    with open(ontology_path, "r") as f:
        ontology_access = json.load(f)

    failures = []
    total_validated = 0

    sanitize_log_file(log_path)
    with open(log_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)  # comma-delimited, don't override with \t
        headers = reader.fieldnames
        if headers is None or "event" not in headers:
            raise ValueError(f"Expected 'event' in headers, but got: {headers}")

        print("Detected headers:", headers)

        for row in reader:
            if not row:
                continue
            event = row.get("event", "").strip()
            validated = row.get("validated", "").strip().upper()
            if event == "memory_update" and validated == "TRUE":
                total_validated += 1
                agent_id = row.get("agent", "").strip()
                key = row.get("key", "").strip()
                prefix = key.split("@")[0]
                allowed = ontology_access.get(agent_id, [])
                if prefix not in allowed:
                    failures.append({
                        "tick": row.get("tick", "").strip(),
                        "agent": agent_id,
                        "key": key
                    })

    failed_count = len(failures)
    score = 1 - failed_count / total_validated if total_validated else 1

    return {
        "total_validated_updates": total_validated,
        "coherence_violations": failed_count,
        "coherence_score": round(score, 3),
        "failures": failures
    }


def evaluate_causal_isolation(log_dir=BASE):
    ontology_path = os.path.join(log_dir, "ontology_access.json")
    log_path = os.path.join(log_dir, "update_log.csv")

    if not os.path.exists(ontology_path):
        raise FileNotFoundError("ontology_access.json not found in logs folder")
    if not os.path.exists(log_path):
        raise FileNotFoundError("update_log.csv not found in logs folder")

    with open(ontology_path, "r") as f:
        ontology_access = json.load(f)

    total_validated = 0
    violations = []

    sanitize_log_file(log_path)
    with open(log_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not row:
                continue
            event = row.get("event", "").strip().lower()
            validated = row.get("validated", "").strip().upper()
            if event == "memory_update" and validated == "TRUE":
                total_validated += 1
                agent_id = row.get("agent", "").strip()
                key = row.get("key", "").strip()
                prefix = key.split("@")[0]
                allowed = ontology_access.get(agent_id, [])
                if prefix not in allowed:
                    violations.append({
                        "tick": row.get("tick", "").strip(),
                        "agent": agent_id,
                        "key": key
                    })

    score = 1 - len(violations) / total_validated if total_validated else 1

    return {
        "total_validated_updates": total_validated,
        "causal_violations": len(violations),
        "isolation_score": round(score, 3),
        "violations": violations
    }


if __name__ == "__main__":
    print("Evaluating theorem compliance from current logs folder...\n")

    print("Semantic Coherence:")
    coh = evaluate_semantic_coherence()
    print(json.dumps(coh, indent=2))

    print("\nCausal Isolation:")
    iso = evaluate_causal_isolation()
    print(json.dumps(iso, indent=2))