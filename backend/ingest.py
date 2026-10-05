import os
import hashlib
import pdfplumber
import psycopg2
import re
from db import get_db_connection

DATA_DIR = "data"

def get_file_hash(filepath):
    """Generate SHA256 to use as the document ID."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def clean_pdf_text(text: str) -> str:
    if not text:
        return ""

    # remove font/ligature encoding
    text = re.sub(r'\(cid:\d+\)', '', text)

    # remove fix words split
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

    # add space between words
    text = re.sub(r'([a-zA-Z])(\d+)', r'\1 \2', text)

    # collaps all mulit space and new line
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

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
                raw_page_text = page.extract_text(layout=True)

                stop_extraction = False
                valid_lines = []

                if raw_page_text:
                    for line in raw_page_text.split('\n'):
                        alpha_only = re.sub(r'[^a-zA-Z]', '', line).lower()

                        if alpha_only in ['references', 'bibliography', 'authorcontributions', 'literaturecited']:
                            print(f"Hit '{line.strip()}' section on page {page_num + 1}. Stopping extraction for {filename}.")
                            stop_extraction = True
                            break

                        valid_lines.append(line)

                sliced_page_text = '\n'.join(valid_lines)
                cleaned_page_text = clean_pdf_text(sliced_page_text)

                if cleaned_page_text and cleaned_page_text.strip():
                    cursor.execute("""
                        INSERT INTO parent_chunks (document_id, content, page_start, page_end, parent_ordinal)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (doc_id, cleaned_page_text, page_num + 1, page_num + 1, page_num + 1))

                if stop_extraction:
                    break

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