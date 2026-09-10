import os
import pymupdf4llm
from langchain_text_splitters import MarkdownHeaderTextSplitter

def load_pdf_as_markdown(file_path):
    return pymupdf4llm.to_markdown(file_path)

def structural_chunker(markdown_text):
    lines = markdown_text.split('\n')
    chunks = []

    current_header = "Document Start"
    current_content = []

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith('#') and ' ' in stripped_line:
            if current_content:
                chunks.append({
                    "metadata": {"Section": current_header},
                    "text": "\n".join(current_content).strip()
                })
                current_content = []

            current_header = stripped_line.lstrip('#').strip()

        else:
            if stripped_line:
                current_content.append(stripped_line)

    if current_content:
        chunks.append({
            "metadata": {"Section": current_header},
            "text": "\n".join(current_content).strip()
        })

    return chunks

def lang_chain_chunker(markdown_text):
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=True
    )

    structural_chunks = markdown_splitter.split_text(markdown_text)

    return structural_chunks

current_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(current_dir, "..", "data", "harries2015.pdf")
pdf_path = os.path.abspath(pdf_path)

try:
    print(f"Extracting layout from: {pdf_path}...")
    raw_markdown = load_pdf_as_markdown(pdf_path)

    my_chunks = structural_chunker(raw_markdown)
    # my_chunks = lang_chain_chunker(raw_markdown)

    print(f"\nSuccessfully created {len(my_chunks)} structurally aware chunks!\n")

    for index, chunk in enumerate(my_chunks[:len(my_chunks)]):
        print(f"--- Chunk {index + 1} ---")

        print(f"METADATA: {chunk['metadata']}")
        # print(f"METADATA: {chunk.metadata}")

        snippet = chunk['text'].replace('\n', ' ')
        # snippet = chunk.page_content.replace('\n', ' ')
        print(f"CONTENT:  {snippet}...\n")

except FileNotFoundError:
    print(f"Error: Could not find '{pdf_path}'.")
