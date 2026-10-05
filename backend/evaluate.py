import json
import os 
import re
from db import get_db_connection
from sentence_transformers import SentenceTransformer

print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def normalize_filename(name: str) -> str:
    # strips spaces, underscores, and hyphens
    return re.sub(r'[\s_\-]+', '', name.lower())

def evaluate_retrieval(dataset_path="eval_dataset.json", top_k=3):
    if not os.path.exists(dataset_path):
        print(f"Evaluation file '{dataset_path}' not found")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    conn = get_db_connection()
    if not conn:
        print("Could not connect to database")
        return

    cursor = conn.cursor()

    hits = 0
    reciprocal_ranks = []
    failed_queries = []

    print(f"\nRunning retrieval evaluation on {len(test_cases)} test cases (TOP K = {top_k})...\n")

    for test_case in test_cases:
        qid = test_case["id"]
        question = test_case["question"]
        expected_file = test_case["expected_filename"]
        expected_pages = test_case.get("expected_pages", [])

        query_vector = model.encode(question).tolist()

        cursor.execute("""
            SELECT
                d.source_filename,
                p.page_start,
                c.content
            FROM child_chunks c
            JOIN parent_chunks p ON c.parent_id = p.parent_id
            JOIN documents d ON p.document_id = d.document_id
            ORDER BY c.embedding::text::vector <=> %s::text::vector
            LIMIT %s
        """, (json.dumps(query_vector), top_k))

        retrieved_rows = cursor.fetchall()

        rank_found = None
        for rank, row in enumerate(retrieved_rows, start=1):
            retrieved_file = row[0]
            retrieved_page = row[1]

            file_match = normalize_filename(expected_file) in normalize_filename(retrieved_file)
            page_match = len(expected_pages) == 0 or (retrieved_page in expected_pages)

            if file_match and page_match:
                rank_found = rank
                break

        if rank_found is not None:
            hits += 1
            rr = 1.0 / rank_found
            reciprocal_ranks.append(rr)
            print(f"Q{qid:02d}: Hit at Rank {rank_found} (RR = {rr:.2f})")
        else:
            reciprocal_ranks.append(0.0)
            failed_queries.append({
                "id": qid,
                "question": question,
                "expected": f"{expected_file} (Pages {expected_pages})",
                "retrieved": [(r[0], r[1]) for r in retrieved_rows]
            })
            print(f"Q{qid:02d}: Missed in top {top_k}")

    total = len(test_cases)
    if total > 0:
        hit_rate = (hits / total) * 100
        mrr = (sum(reciprocal_ranks) / total)
    else:
        hit_rate = 0 
        mrr = 0

    print("RETRIEVAL EVALUATION SUMMARY")
    print(f"Total Test Cases : {total}")
    print(f"Hit Rate @ {top_k}    : {hit_rate:.1f}% ({hits}/{total})")
    print(f"MRR @ {top_k}         : {mrr:.3f}")

    if failed_queries:
        print("\n MISSED QUERIES DIAGNOSTIC:")
        for fq in failed_queries:
            print(f"\n[Q{fq['id']:02d}] \"{fq['question']}\"")
            print(f"   Expected  : {fq['expected']}")
            print("   Retrieved :")
            for r in fq['retrieved']:
                print(f"     - {r[0]} (Page {r[1]})")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    evaluate_retrieval(top_k=3)
