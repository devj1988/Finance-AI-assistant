# from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
# from utils import urls
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_ollama import OllamaEmbeddings

load_dotenv()  # take environment variables from .env file

# embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# embeddings = OllamaEmbeddings(
#     model="llama3",
# )

all_urls=[
        "https://www.investopedia.com/personal-finance-4427760",
        "https://www.investopedia.com/budgeting-and-savings-4427755",
        "https://www.investopedia.com/personal-loans-4689729",
        "https://www.investopedia.com/insurance-4427716",
        "https://www.investopedia.com/mortgage-4689703",
        "https://www.investopedia.com/credit-and-debt-4689724",
        "https://www.investopedia.com/student-loans-4689727",
        "https://www.investopedia.com/taxes-4427724",
        "https://www.investopedia.com/credit-card-4689721",
        "https://www.investopedia.com/financial-literacy-resource-center-7151950",
        "https://www.investopedia.com/financial-literacy-resource-center-7151950"
    ]

from langchain_chroma import Chroma

def create_vector_store():
    """Search for relevant documents."""
    # Load documents
    urls=[
        "https://www.investopedia.com/personal-finance-4427760",
        "https://www.investopedia.com/budgeting-and-savings-4427755",
        "https://www.investopedia.com/personal-loans-4689729",
        "https://www.investopedia.com/insurance-4427716",
        "https://www.investopedia.com/mortgage-4689703"
    ]
    loader = UnstructuredURLLoader(urls=urls)
    docs = loader.load()
    
    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    doc_splits = text_splitter.split_documents(docs)

    # Create VectorStore
    print("Creating new vector store and persisting to disk...")
    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        collection_name="finance_docs",
        embedding=embeddings,
        persist_directory="../data/chroma_db"
    )

    return vectorstore

vector_store = create_vector_store()

while True:
    q = input("Enter your query (or 'exit' to quit): ")
    if q.lower() == 'exit':
        break
    print("Querying vector store...")
    retriever = vector_store.as_retriever(
    search_type="mmr", search_kwargs={"k": 1, "fetch_k": 5}
    )
    print(retriever.invoke(q))
