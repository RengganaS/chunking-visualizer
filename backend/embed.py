import json
from db import get_db_connection
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# load embedding model
print("Load embedding model")
model_name = 'all-MiniLM-L6-v2'
model = SentenceTransformer(model_name)

# set up chunker
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1000,
    chunk_overlap = 200,
    length_function = len
)

def process_embedding():
    conn = get_db_connection()
    if not conn:
        print("Could not connect to database")
        return

    cursor = conn.cursor()

    # fetch parent chunks
    cursor.execute("""
        SELECT p.parent_id, p.document_id, p.content, d.source_filename
        FROM parent_chunks p
        JOIN documents d ON p.document_id = d.document_id
        LEFT JOIN child_chunks c ON p.parent_id = c.parent_id
        WHERE c.child_id IS NULL
    """)

    parents = cursor.fetchall()
    if not parents:
        print("No new chunks to process")
        return

    print(f"Found {len(parents)} pages to chunk and embed")

    for parent in parents:
        parent_id = parent[0]
        doc_id = parent[1]
        content = parent[2]
        filename = parent[3]

        # break page into chunks
        chunks = text_splitter.split_text(content)

        for i, chunk_text in enumerate(chunks):
            # ignore chunks under 10 or only numbers
            clean_text = chunk_text.strip()
            if len(clean_text) < 10 or clean_text.isdigit():
                continue

            embedding_vector = model.encode(chunk_text).tolist()
            token_count = int(len(chunk_text.split()) * 1.3)

            cursor.execute("""
                INSERT INTO child_chunks (parent_id, document_id, child_ordinal, content, token_count, embedding_model, embedding, embedded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (parent_id, doc_id, i + 1, chunk_text, token_count, model_name, json.dumps(embedding_vector)))

        conn.commit()
        print(f"Chunked page from {filename} into {len(chunks)} child chunks")

    cursor.close()
    conn.close()
    print("Embedding complete")

if __name__ == "__main__":
    process_embedding()


