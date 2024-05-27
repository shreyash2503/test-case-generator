#####
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_groq import ChatGroq
import google.generativeai as genai
from langchain_community.vectorstores.faiss import FAISS
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Setting Google API Key
load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

DB_FAISS_PATH = 'vectorstore/db_faiss'

chat_history=[]

#Loading the model
def load_llm():
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=1, max_output_tokens=1000)
    return llm

def history_aware_retriever(retriever, llm):
    contextualize_q_system_prompt = """Given a chat history and the latest user question \
    which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, \
    just reformulate it if needed and otherwise return it as is."""
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )
    
    return history_aware_retriever

# Setting QA chain
def get_conversational_chain(history_aware_retriever, llm):
    use_case_system_prompt = """You are an assistant designed to help generate use cases from Software Requirements Specifications (SRS) documents. 
    Use the following pieces of context to create detailed and comprehensive use cases based on the information provided in the SRS document. 
    If any information is missing or unclear, please note that in your response. 
    Keep the use cases structured, precise, and aligned with standard use case formats. Always provide a professional and helpful response.

    {context}"""
    use_case_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", use_case_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    use_case_chain = create_stuff_documents_chain(llm, use_case_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, use_case_chain)
    
    return rag_chain

# Function to process SRS document and generate use cases
def generate_use_cases(srs_document):
    print(srs_document)
    user_question = "Generate use cases from the following SRS document."
    # Set google embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    
    # Loading saved vectors from local path
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever()
    
    llm = load_llm()
    
    history_retriever = history_aware_retriever(retriever, llm)
    rag_chain = get_conversational_chain(history_retriever, llm)
    
    response = rag_chain.invoke({"input": "Generate test cases for the following SRS document for the functional requirements in the document \n" + srs_document, "chat_history": chat_history})
    chat_history.extend([HumanMessage(content=user_question), response["answer"]])

    print(response["answer"])
    
    return response["answer"]

# FastAPI initialization
app = FastAPI()

# API endpoint (POST Request)
@app.post("/generate_use_cases")
async def final_result(file: UploadFile = File(...)):
    srs_content = await file.read()
    srs_document = srs_content.decode("utf-8")
    use_cases = generate_use_cases(srs_document)
    return {"use_cases": use_cases}
