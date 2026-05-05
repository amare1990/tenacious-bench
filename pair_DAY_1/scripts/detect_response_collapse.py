import json
import os

import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
TRACE_PATH = os.path.join(BASE_DIR, "held_out_traces.jsonl")


def load_traces(path):
    traces = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            output = (
                row.get("model_output")
                or row.get("output")
                or row.get("response")
                or row.get("assistant_response")
            )
            if output:
                row["normalized_output"] = output
                traces.append(row)
    return traces


def detect_response_collapse(responses, threshold=0.90):
    if len(responses) < 2:
        return {
            "num_responses": len(responses),
            "avg_pairwise_similarity": None,
            "collapse_detected": False,
            "most_similar_pair": None,
        }

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(responses, normalize_embeddings=True)
    sim_matrix = embeddings @ embeddings.T
    np.fill_diagonal(sim_matrix, 0)

    n = len(responses)
    avg_sim = sim_matrix.sum() / (n * (n - 1))
    most_similar_pair = tuple(
        map(int, np.unravel_index(sim_matrix.argmax(), sim_matrix.shape))
    )

    return {
        "num_responses": n,
        "avg_pairwise_similarity": round(float(avg_sim), 4),
        "collapse_detected": bool(avg_sim > threshold),
        "most_similar_pair": most_similar_pair,
    }


def group_by_condition(traces):
    groups = {}
    for trace in traces:
        condition = trace.get("condition", "unknown")
        groups.setdefault(condition, []).append(trace["normalized_output"])
    return groups


if __name__ == "__main__":
    traces = load_traces(TRACE_PATH)

    all_outputs = [trace["normalized_output"] for trace in traces]
    print("GLOBAL")
    print(detect_response_collapse(all_outputs))

    print("\nBY CONDITION")
    for condition, outputs in group_by_condition(traces).items():
        print(condition)
        print(detect_response_collapse(outputs))