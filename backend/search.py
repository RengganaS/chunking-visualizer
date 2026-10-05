import json
from db import get_db_connection
from sentence_transformers import SentenceTransformer

print("Load Embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def search_pappers(question, top_k=3):
    conn = get_db_connection()
    if not conn:
        print("Could not connect to database")
        return

    cursor = conn.cursor()

    print(f"Searching for: '{question}'\n")

    query_vector = model.encode(question).tolist()

    # semantic search using cosine distance
    try:
        cursor.execute("""
            SELECT 
                c.content AS exact_match,
                p.content AS full_page,
                d.source_filename,
                p.page_start
            FROM child_chunks c
            JOIN parent_chunks p ON c.parent_id = p.parent_id
            JOIN documents d ON p.document_id = d.document_id
            ORDER BY c.embedding::text::vector <=> %s::text::vector
            LIMIT %s
        """, (json.dumps(query_vector), top_k))

        results = cursor.fetchall()

        if not results:
            print("No matches found.")
            return

        print(f"TOP {top_k} RESULTS FOUND")

        for i, row in enumerate(results):
            child_text = row[0]
            parent_text = row[1]
            filename = row[2]
            page_num = row[3]

            print(f"\nMATCH #{i+1}")
            print(f"Source: {filename} (Page {page_num})")
            print("-" * 60)
            print(f"Child Chunk that matched:")
            print(f"{child_text}\n")
            
            print(f"First 250 chars of the Parent Page:")
            clean_parent = parent_text.strip()
            print(f"{clean_parent[:250]}...\n")

    except Exception as e:
        print("\n Search Error:", e)
        print("Hint: If you see an error about 'type vector does not exist', we need to enable the pgvector extension in your database!")

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    question = "How was RPE used for autoregulation?"
    search_pappers(question)



 