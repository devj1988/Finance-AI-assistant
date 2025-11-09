from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

load_dotenv()  # take environment variables from .env file

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

from langchain_chroma import Chroma

def create_vector_store():
    """Search for relevant documents."""
    # Example URL configuration
    urls = [
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
    # Load documents
    loader = UnstructuredURLLoader(urls=urls)
    docs = loader.load()
    
    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    doc_splits = text_splitter.split_documents(docs)
    

    if (os.path.exists("./chroma_db")):
        print("Loading existing vector store from disk...")
        vectorstore = Chroma(
            collection_name="python_docs",
            embedding_function=OpenAIEmbeddings(),
            persist_directory="./chroma_db"
        )
        return vectorstore

    # Create VectorStore
    print("Creating new vector store and persisting to disk...")
    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        collection_name="python_docs",
        embedding=OpenAIEmbeddings(),
        persist_directory="./chroma_db"
    )

    return vectorstore

def invoke_retrieval(query: str, vectorstore: Chroma):
    """Invoke retrieval for a given query."""
    retriever = vectorstore.as_retriever()
    results = retriever.invoke(query)
    return "\n".join([doc.page_content for doc in results])


vector_store = create_vector_store()

print(invoke_retrieval("What is the best way to invest for retirement?", vector_store))