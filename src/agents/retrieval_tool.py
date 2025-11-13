# from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os, json
# from utils import urls
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.tools import tool

load_dotenv()  # take environment variables from .env file

# embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

from langchain_chroma import Chroma

def get_vector_store():
    if (os.path.exists("./data/chroma_db")):
        print("Loading existing vector store from disk...")
        vectorstore = Chroma(
            collection_name="finance_docs",
            embedding_function=embeddings,
            persist_directory="./data/chroma_db"
        )
        return vectorstore
    else:
        raise ValueError("Vector store not found. Please create the vector store first.")

def invoke_retrieval(query: str, retriever: any):
    """Invoke retrieval for a given query."""
    print(f"Invoking retrieval for query: {query}")
    results = retriever.invoke(query)
    ret = "\n".join([doc.page_content for doc in results])
    print("---- Retrieved documents ----")
    print(f"Retrieved documents: {results}")
    print("---- End of retrieved documents ----")
    return ret

def invoke_retrieval2(query: str, retriever: any):
    """Invoke retrieval for a given query."""
    print(f"Invoking retrieval for query: {query}")
    results = retriever.invoke(query)
    json_dict = [{ "source": doc.metadata['source'], "content":  doc.page_content } for doc in results]
    print(json_dict)
    ret = json.dumps(json_dict)
    print("---- Retrieved documents ----")
    print(f"Retrieved documents: {ret}")
    print("---- End of retrieved documents ----")
    return ret

vector_store = get_vector_store()
retriever = vector_store.as_retriever()

@tool
def retrieve_documents(query: str) -> str:
     """
     Retrieve finance related documents for a given query.
     """
     return invoke_retrieval2(query, retriever)

# print(retrieve_documents.invoke("What is personal finance?"))