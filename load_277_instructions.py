from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

loader = PyPDFLoader("277_response_understanding.pdf")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

pdf_chunks = splitter.split_documents(docs)

for doc in pdf_chunks:
    doc.metadata.update({
        "source": "277_PDF",
        "type": "REJECTION_GUIDE"
    })