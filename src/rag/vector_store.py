# from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
# from utils import urls
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from urls import investopedia_urls, boglehead_urls
from uuid import uuid4
from langchain_core.documents import Document
import time
import chromadb

load_dotenv()  # take environment variables from .env file

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

VECTOR_STORE_PATH = "../data/investopedia_chroma_db-nov-21-2024_2" 
COLLECTION_NAME = "finance_docs"

def get_vector_store(dbpath, collection_name):
    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=dbpath,
    )

    return vector_store

def count_documents(dbpath, collection_name):
    """Count documents in the Chroma collection."""

    client = chromadb.Client()
    client = chromadb.PersistentClient(path=dbpath)
    collection = client.get_collection(collection_name)
    print("Collection name:", collection.name)
    print("Number of documents in collection:", collection.count())

def add_documents_to_vector_store(vector_store, documents, uuids, after=1, max_retries=5, max_sleep=180):
    """Add documents to the vector store."""
    try:
        vector_store.add_documents(documents=documents, ids=uuids)
    except Exception as e:
        print(f"Error adding documents to vector store: , will sleep for {pow(3, after)} seconds", e)
        time.sleep(min(pow(3, after), max_sleep))
        if after <= max_retries:
            add_documents_to_vector_store(vector_store, documents, uuids, after + 1)
        else:
            raise e


def create_vector_store_from_urls():
    """Search for relevant documents."""
    # Load documents
    vector_store = get_vector_store(VECTOR_STORE_PATH, COLLECTION_NAME)
    count_documents(VECTOR_STORE_PATH, COLLECTION_NAME)
    all_urls = investopedia_urls
    batch_size = 1
    print(f"Total URLs to process: {len(all_urls)}")
    print(f"Batch size: {batch_size}")
    print("Number of batches:", (len(all_urls) + batch_size - 1) // batch_size)
    print("-----------------------------")
    print("Starting document retrieval and vector store creation...")
    i = 0
    while i < len(all_urls):
        print(f"Processing URLs {i} to {i + batch_size}...")
        docs = retrieve_and_chunk_documents(all_urls[i:i + batch_size])
        uuids = [str(uuid4()) for _ in range(len(docs))]
        add_documents_to_vector_store(vector_store, docs, uuids)
        i += batch_size
        time.sleep(10)  # Sleep to avoid overwhelming any servers
    count_documents(VECTOR_STORE_PATH, COLLECTION_NAME)


def create_vector_store_from_files():
    vector_store = get_vector_store(VECTOR_STORE_PATH, COLLECTION_NAME)
    count_documents(VECTOR_STORE_PATH, COLLECTION_NAME)
    
    docs = load_document_from_file("./kb/boglehead/")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    doc_splits = text_splitter.split_documents(docs)

    batch_size = 5
    print(f"Total documents after splitting: {len(doc_splits)}")

    for i in range(0, len(doc_splits), batch_size):
        print(f"Processing documents {i} to {i + batch_size}...")
        batch_docs = doc_splits[i:i + batch_size]
        uuids = [str(uuid4()) for _ in range(len(batch_docs))]
        add_documents_to_vector_store(vector_store, docs, uuids, max_retries=8)
        # vector_store.add_documents(documents=batch_docs, ids=uuids)
        time.sleep(10)  # Sleep to avoid overwhelming any servers
    count_documents(VECTOR_STORE_PATH, COLLECTION_NAME)


def retrieve_and_chunk_documents(urls):
    docs = load_doc_from_url(urls)

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    doc_splits = text_splitter.split_documents(docs)

    print(doc_splits[0])

    print(f"Total documents after splitting: {len(doc_splits)}")

    return doc_splits

def load_doc_from_url(urls):
    custom_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    # Create a headers dictionary
    headers = {"User-Agent": custom_user_agent}
    loader = UnstructuredURLLoader(urls=urls, headers=headers)
    docs = loader.load()
    return docs

def query_vector_store():
    while True:
        q = input("Enter your query (or 'exit' to quit): ")
        if q.lower() == 'exit':
            break
        print("Querying vector store...")
        retriever = get_vector_store(VECTOR_STORE_PATH, COLLECTION_NAME).as_retriever(
            search_type="mmr", search_kwargs={"k": 1, "fetch_k": 5}
        )
        print(retriever.invoke(q))

# create_vector_store()

# query_vector_store()

def load_document_from_file(dir_path):
    from langchain_community.document_loaders import BSHTMLLoader
    import os
    visible_files_only = [f for f in os.listdir(dir_path)
                      if not f.startswith('.') and
                      os.path.isfile(os.path.join(dir_path, f))]

    docs = []
    for i in range(len(visible_files_only)):
        loader = BSHTMLLoader(
            file_path=os.path.join(dir_path, visible_files_only[i]),
        )
        # print(visible_files_only[i])
        idx_in_boglehead_urls = int(visible_files_only[i].split(".")[0]) - 1
        # print("Index in boglehead URLs:", idx_in_boglehead_urls)
        # print("Corresponding URL:", boglehead_urls[idx_in_boglehead_urls])
        doc = loader.load()
        doc[0].metadata["source"] = boglehead_urls[idx_in_boglehead_urls]
        # print(doc[0].page_content[:50])
        docs.append(doc[0])
    return docs


create_vector_store_from_files()
# create_vector_store_from_urls()