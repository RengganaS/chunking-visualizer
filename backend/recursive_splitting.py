import os
import pypdf

def load_pdf_text(file_path):
    extracted_text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = pypdf.PdfReader(file)
        for page in pdf_reader.pages:
            extracted_text += page.extract_text() + "\n"
    return extracted_text

def recursive_chunker(text, chunk_size, seperators=["\n\n", "\n", " ", ""]):
    seperator = seperators[0]
    splits = text.split(seperator)

    final_chunks = []
    current_chunk = ""

    for split in splits:
        if len(split) > chunk_size:
            if current_chunk:
                final_chunks.append(current_chunk)
                current_chunk = ""

            if len(seperators) > 1:
                nested_chunks = recursive_chunker(split, chunk_size, seperators[1:])
                final_chunks.extend(nested_chunks)
            else:
                final_chunks.append(split[:chunk_size])

        else:
            if len(current_chunk) + len(seperator) + len(split) <= chunk_size:
                if current_chunk:
                    current_chunk += seperator
                current_chunk += split
            else:
                if current_chunk:
                    final_chunks.append(current_chunk)
                current_chunk = split

    if current_chunk:
        final_chunks.append(current_chunk)

    return final_chunks

current_pdf = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(current_pdf, "..", "data", "atletPov_powerbuilding.pdf")
pdf_path = os.path.abspath(pdf_path)

try:
    print(f"Attempting to load: {pdf_path}...")
    raw_document_string = load_pdf_text(pdf_path)

    my_chunks = recursive_chunker(raw_document_string, chunk_size=1000)

    print(f"Successfully created {len(my_chunks)} chunks!\n")

    for index, chunk in enumerate(my_chunks[:len(my_chunks)]):
        print(f"--- Chunk {index + 1} (Words: {len(chunk.split())}) ---")
        print(chunk.strip())
        print("-" * 40 + "\n")

except FileNotFoundError:
    print(f"Error: Could not find '{pdf_path}'.")
