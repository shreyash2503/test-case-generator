
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
import google.generativeai as genai
import os
from dotenv import load_dotenv

DATA_PATH = 'data/'

DB_FAISS_PATH = 'vectorstore/db_faiss'


load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Create vector database
def create_vector_db():

    loader = DirectoryLoader(DATA_PATH,
                             glob='*.pdf',
                             loader_cls=PyPDFLoader)

    documents = loader.load()
    
    print(len(documents))
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
                                                   chunk_overlap=200)
    texts = text_splitter.split_documents(documents)

    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    
    db = FAISS.from_documents(texts, embeddings)
    
    db.save_local(DB_FAISS_PATH)
    print("Succesfully made and saved text embeddings!")

if __name__ == "__main__":
    create_vector_db()