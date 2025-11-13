# from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain_chroma import Chroma
import os, json
# from utils import urls
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.tools import tool
from langchain_chroma import Chroma

load_dotenv()  # take environment variables from .env file

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


VECTOR_STORE_PATH="./data/boglehead_chroma_db-nov-11-2025"

def get_vector_store():
    if (os.path.exists(VECTOR_STORE_PATH)):
        print("Loading existing vector store from disk...")
        vectorstore = Chroma(
            collection_name="finance_docs",
            embedding_function=embeddings,
            persist_directory=VECTOR_STORE_PATH
        )
        return vectorstore
    else:
        raise ValueError("Vector store not found. Please create the vector store first.")

def invoke_retrieval(query: str, retriever: any):
    """Invoke retrieval for a given query."""
    print(f"Invoking retrieval for query: {query}")
    results = retriever.invoke(query)
    print(f"Number of documents retrieved: {len(results)}")
    json_dict = [{ "source": doc.metadata['source'], "content":  doc.page_content } for doc in results]
    # print(json_dict)
    ret = json.dumps(json_dict)
    # print("---- Retrieved documents ----")
    # print(f"Retrieved documents: {ret}")
    # print("---- End of retrieved documents ----")
    return ret

vector_store = get_vector_store()
MAX_DOCS = 5
retriever = vector_store.as_retriever(search_kwargs={"k": MAX_DOCS})

@tool
def retrieve_documents(query: str) -> str:
     """
     Retrieve finance related documents for a given query.
     """
     return invoke_retrieval(query, retriever)

# print(retrieve_documents.invoke("What is personal finance?"))