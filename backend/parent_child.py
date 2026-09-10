import  os
import uuid
import pymupdf4llm
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
    ("####", "Header 4"),
]

structural_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
    strip_headers=True
)

parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=200)

def build_hierarchical_database(markdown_text):
    parent_document_store = {}
    child_vector_store = []

    structural_docs = structural_splitter.split_text(markdown_text)

    parents_docs =  parent_splitter.split_documents(structural_docs)
    for p_doc in parents_docs:
        parent_id = str(uuid.uuid4())

        parent_document_store[parent_id] = {
            "text": p_doc.page_content,
            "metadata": p_doc.metadata
        }

        child_chunks = child_splitter.split_text(p_doc.page_content)

        for child_text in child_chunks:
            child_vector_store.append({
                "parent_id": parent_id,
                "text": child_text,
                "metadata": p_doc.metadata
            })

    return parent_document_store, child_vector_store

current_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(current_dir, "..", "data", "harries2015.pdf")
pdf_path =  os.path.abspath(pdf_path)

try:
    print(f"Reading: {pdf_path}...\n")
    raw_markdown = pymupdf4llm.to_markdown(pdf_path)

    parents_db, children_db = build_hierarchical_database(raw_markdown)

    print(f"Created {len(parents_db)} Massive Parent Chunks.")
    print(f"Created {len(children_db)} Tiny Child Chunks.\n")
    print("=" * 60)

    # see inside of parent and child text
    first_parent_id = list(parents_db.keys())[0]
    first_parent = parents_db[first_parent_id]

    first_parent_content = first_parent["text"]
    first_parent_metadata = first_parent["metadata"]

    print(f"PARENT CHUNK (ID: {first_parent_id})")
    print(f"Metadata: {first_parent_metadata}")
    print(f"Length: {len(first_parent_content)} chars")
    print(f"Content:\n{first_parent_content[:300]}...\n")
    print("-" * 60)

    child_counter = 1
    for child in children_db:
        if child["parent_id"] == first_parent_id:
            print(f"   CHILD {child_counter} (Linked to Parent: {child['parent_id']})")
            print(f"   Length: {len(child['text'])} chars")

            print(f"   Length: {len(child['text'])} chars")
            child_counter += 1

    print("=" * 60)

    print("\n--- SIMULATING VECTOR SEARCH ---")

    retrieved_child = children_db[4]
    found_parent_id =  retrieved_child["parent_id"]

    print(f"1. Search matched a small chunk (Length: {len(retrieved_child['text'])} chars)")
    print(f"   Child Text: {retrieved_child['text'][:100]}...\n")

    print(f"2. Child is demanding Parent ID: {found_parent_id}")

    retrieved_parent = parents_db[found_parent_id]

    print(f"3. Parent retrieved! Sending {len(retrieved_parent)} characters of context to the LLM.")

except FileNotFoundError:
    print(f"Error: Could not find '{pdf_path}'.")

    

        