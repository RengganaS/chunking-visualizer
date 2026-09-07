from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

def test_naive_chunking():
    # hardcode file input
    pdf_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'harries2015.pdf')

    loader = UnstructuredPDFLoader(pdf_path)
    docs = loader.load()

    # slicing text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 5,
        length_function= len
    )

    chunks = text_splitter.split_documents(docs)

    print(f"Document succesfully split into {len(chunks)} chunks.\n")

    # visualize output
    for i, chunk in enumerate(chunks):
        print(f"=== Chunk {i+1} (Length: {len(chunk.page_content)}) ===")
        print(chunk.page_content)
        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    test_naive_chunking()