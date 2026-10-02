import os
import pymupdf
import csv
import hashlib

DATA_DIR = "data"
OUTPUT_CSV = "audit_report.csv"

def get_file_hash(filepath):
    """Generate SHA256 for the document to match the database scheme."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def audit_pdf(filepath):
    filename = os.path.basename(filepath)
    doc_hash = get_file_hash(filepath)

    try:
        doc = pymupdf.open(filepath)
    except Exception as e:
        return {"filename": filename, "status": f"Corrupt or unreadable: {e}"}

    page_count = len(doc)
    total_text_length = 0
    total_images = 0
    needs_ocr = False
    has_complex_layout = False

    # sample 5 pages
    pages_to_check = min(5, page_count)

    for page_num in range(pages_to_check):
        page = doc[page_num]

        # check selectable text
        text = page.get_text("text")
        total_text_length += len(text)

        # check for images
        image_list = page.get_images(full=True)
        total_images += len(image_list)

        # check for Tables
        blocks = page.get_text("blocks")
        if len(blocks) > 15:
            has_complex_layout = True

    doc.close()

    if pages_to_check > 0:
        avg_chars_per_page = total_text_length / pages_to_check
    else:
        avg_chars_per_page = 0

    if avg_chars_per_page < 150 and total_images > 0:
        needs_ocr = True

    return {
        "filename": filename,
        "sha256": doc_hash,
        "pages": page_count,
        "avg_chars_per_page": round(avg_chars_per_page),
        "total_images_in_sample": total_images,
        "complex_layout": has_complex_layout,
        "needs_ocr": needs_ocr,
        "status": "Success"
    }

def main():
    if not os.path.exists(DATA_DIR):
        print(f"Directory '{DATA_DIR}' not found.")
        return

    results = []
    for file in os.listdir(DATA_DIR):
        if file.lower().endswith(".pdf"):
            filepath = os.path.join(DATA_DIR, file)
            print(f"Auditing {file}...")
            results.append(audit_pdf(filepath))

    if results:
        keys = ["filename", "sha256", "pages", "avg_chars_per_page", "total_images_in_sample", "complex_layout", "needs_ocr", "status"]
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(results)
        print(f"\nAudit complete. Results saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()

