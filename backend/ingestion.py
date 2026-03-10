import os
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def load_documents(folder_path):
    documents = []

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return []

    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(folder_path, file)
            reader = PdfReader(pdf_path)

            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""

            # Create a Document object with metadata
            doc = Document(page_content=text, metadata={"source": file})
            documents.append(doc)

    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = []
    for doc in documents:
        # split_documents method handles list of Documents and preserves metadata
        chunks.extend(splitter.split_documents([doc]))

    return chunks
