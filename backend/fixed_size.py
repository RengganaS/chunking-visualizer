import os
import pypdf

def load_pdf_text(file_path):
    extracted_text = ""

    with open(file_path, 'rb') as file:
        pdf_reader = pypdf.PdfReader(file)

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]

            extracted_text += page.extract_text() + " "

    return extracted_text

def fixed_size(text, chunk_size, overlap):
    if overlap > chunk_size:
        raise ValueError("Overlap must strictly less than chunk size.")

    words = text.split()
    total_words = len(words)
    stride = chunk_size - overlap
    chunks = []

    for i in range(0, total_words, stride):
        chunk_slice = words[i : i + chunk_size]
        chunk_text = " ".join(chunk_slice)
        chunks.append(chunk_text)

        if (i + chunk_size) >= total_words:
            break

    return chunks

current_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(current_dir, "..", "data", "harries2015.pdf")
pdf_path = os.path.abspath(pdf_path)

try:
    print(f"Attempting to load: {pdf_path}...")
    raw_document_string = load_pdf_text(pdf_path)

    my_chunks = fixed_size(raw_document_string, chunk_size=200, overlap=40)

    print(f"Successfully created {len(my_chunks)} chunks!\n")

    for index, chunk in enumerate(my_chunks[:len(my_chunks)]):
        print(f"--- Chunk {index + 1} (Words: {len(chunk.split())}) ---")
        print(chunk)
        print("-" * 40 + "\n")

except FileNotFoundError:
    print(f"Error: Could not find '{pdf_path}'.")






