import os
import hashlib
import pdfplumber
import psycopg2
from db import get_db_connection

DATA_DIR = "data"

def get_file_hash(filepath):
    """Generate SHA256 to use as the document ID."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def process_pdf(filepath, conn):
    filename = os.path.basename(filepath)
    doc_id = get_file_hash(filepath)
    cursor = conn.cursor()

    # check document
    cursor.execute("SELECT document_id FROM documents WHERE document_id = %s", (doc_id,))
    if cursor.fetchone():
        print(f"Skipping {filename} (Already in database)")
        cursor.close()
        return

    print(f"Processing {filename}")

    try:
        with pdfplumber.open(filepath) as pdf:
            page_count = len(pdf.pages)

            # insert into documents table
            cursor.execute("""
                INSERT INTO documents (document_id, source_sha256, source_filename, page_count, extraction_method)
                VALUES (%s, %s, %s, %s, %s)
            """, (doc_id, doc_id, filename, page_count, 'pdfplumber_layout'))

            # extract and chunk by page
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text(layout=True)

                if text and text.strip():
                    cursor.execute("""
                        INSERT INTO parent_chunks (document_id, content, page_start, page_end, parent_ordinal)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (doc_id, text, page_num + 1, page_num + 1, page_num + 1))

            cursor.execute("""
                INSERT INTO ingestion_runs (source_filename, source_sha256, extraction_method, status)
                VALUES (%s, %s, %s, %s)
            """, (filename, doc_id, 'pdfplumber_layout', 'Success'))

            conn.commit()
            print(f"Successfully ingested {filename}")
    except Exception as e:
        conn.rollback()
        print(f"Error processing {filename}: {e}")
        cursor.execute("""
            INSERT INTO ingestion_runs (source_filename, source_sha256, extraction_method, status, error_message)
            VALUES (%s, %s, %s, %s, %s)
        """, (filename, doc_id, 'pdfplumber_layout', 'Failed', str(e)))
        conn.commit()
    finally:
        cursor.close()

def main():
    conn = get_db_connection()
    if not conn:
        print("Could not connect to database")
        return

    for file in os.listdir(DATA_DIR):
        if file.lower().endswith(".pdf"):
            filepath = os.path.join(DATA_DIR, file)
            process_pdf(filepath, conn)

    conn.close()
    print("Ingestion complete")

if __name__ == "__main__":
    main()