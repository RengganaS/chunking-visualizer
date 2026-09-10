import  os
import uuid
import pymupdf4llm
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
    ("####", "Header 4"),
    ("#####", "Header 5"),
    ("######", "Header 6"),
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

def evaluate_chunking_quality(child_vector_store):
    total_chunks = len(child_vector_store)
    if total_chunks == 0:
        print("Error: No chunks provided for evaluation.")
        return

    lengths = [len(chunk["text"]) for chunk in child_vector_store]
    min_len = min(lengths)
    max_len = max(lengths)
    avg_len = sum(lengths) // total_chunks

    tiny_chunks = sum(1 for l in lengths if l < 50)
    massive_chunks = sum(1 for l in lengths if l > 1000)

    chunks_with_metadata = sum(1 for chunk in child_vector_store if chunk.get("metadata"))
    metadata_percentage = (chunks_with_metadata / total_chunks) * 100

    print("\n" + "="*40)
    print("CHUNKING DIAGNOSTIC REPORT")
    print("="*40)
    print(f"Total Child Chunks Generated: {total_chunks}")
    
    print("\n--- SIZE DISTRIBUTION ---")
    print(f"Smallest Chunk: {min_len} chars")
    print(f"Largest Chunk:  {max_len} chars")
    print(f"Average Size:   {avg_len} chars")
    print(f"Warning: {tiny_chunks} chunks are dangerously small (< 50 chars).")
    print(f"Warning: {massive_chunks} chunks are dangerously large (> 1000 chars).")

    print("\n--- STRUCTURAL INTEGRITY ---")
    print(f"Metadata Coverage: {metadata_percentage:.1f}%")
    if metadata_percentage < 50:
        print("  -> FAILURE: Most chunks lost their structural context.")
    elif metadata_percentage == 100:
        print("  -> SUCCESS: Every single chunk is mapped to a header.")
        
    print("="*40 + "\n")



current_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(current_dir, "..", "data", "harries2015.pdf")
pdf_path =  os.path.abspath(pdf_path)

try:
    print(f"Reading: {pdf_path}...\n")
    raw_markdown = pymupdf4llm.to_markdown(pdf_path)

    # print("--- RAW MARKDOWN ---")
    # print(raw_markdown[:3000])
    # print("-------------------------\n")

    # clean_markdown = "\n" + raw_markdown.replace('\r\n', '\n').replace('\u200b', '')

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

    evaluate_chunking_quality(children_db)

except FileNotFoundError:
    print(f"Error: Could not find '{pdf_path}'.")

    

        