import os
from io import BytesIO
from typing import List, Optional

import streamlit as st
from docx import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from PyPDF2 import PdfReader
from streamlit.runtime.uploaded_file_manager import UploadedFile

# Initialize OpenAI API key
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("Please set OPENAI_API_KEY in your Streamlit secrets")
    st.stop()

os.environ["OPENAI_API_KEY"] = api_key

SUPPORTED_FORMATS = [".pdf", ".docx", ".txt"]

def parse_docx(file: UploadedFile) -> str:
    try:
        docx_bytes = file.getvalue()
        docx_io = BytesIO(docx_bytes)
        document = Document(docx_io)
        return " ".join([paragraph.text for paragraph in document.paragraphs])
    except Exception as e:
        st.error(f"Error parsing DOCX file: {str(e)}")
        return ""

def get_text(docs: List[UploadedFile]) -> str:
    doc_text = []
    for doc in docs:
        file_ext = os.path.splitext(doc.name)[1].lower()
        if file_ext not in SUPPORTED_FORMATS:
            st.warning(f"Unsupported file format: {file_ext}")
            continue

        try:
            if file_ext == ".pdf":
                pdf_reader = PdfReader(doc)
                doc_text.extend(filter(None, [page.extract_text() for page in pdf_reader.pages]))
            elif file_ext == ".docx":
                doc_text.append(parse_docx(doc))
            elif file_ext == ".txt":
                doc_text.append(doc.getvalue().decode("utf-8"))
        except Exception as e:
            st.error(f"Error processing {doc.name}: {str(e)}")

    return "\n".join(filter(None, doc_text))

def get_chunks(text: str) -> List[str]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    return text_splitter.split_text(text)

def get_vectorstore(chunks: List[str]) -> Optional[FAISS]:
    try:
        return FAISS.from_texts(
            texts=chunks,
            embedding=OpenAIEmbeddings()
        )
    except Exception as e:
        st.error(f"Error creating vector store: {str(e)}")
        return None

def get_conversation_chain(retriever) -> Optional[ConversationalRetrievalChain]:
    try:
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            streaming=True
        )
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        return ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            verbose=True
        )
    except Exception as e:
        st.error(f"Error creating conversation chain: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="ChatDocs", page_icon="📄", layout="wide")
    
    st.title("ChatDocs - Chat with your Documents 📄")

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "doc_len" not in st.session_state:
        st.session_state.doc_len = 0

    with st.sidebar:
        st.subheader("Upload Documents")
        docs = st.file_uploader(
            "Upload documents (PDF, DOCX, TXT)",
            accept_multiple_files=True,
            type=["pdf", "docx", "txt"]
        )

        if docs and len(docs) > st.session_state.doc_len:
            st.session_state.doc_len = len(docs)
            with st.spinner("Processing documents..."):
                # Get document text
                doc_text = get_text(docs)
                if doc_text:
                    # Split into chunks
                    doc_chunks = get_chunks(doc_text)
                    
                    # Create vector store
                    vectorstore = get_vectorstore(doc_chunks)
                    if vectorstore:
                        # Create retriever
                        retriever = vectorstore.as_retriever()
                        
                        # Create conversation chain
                        st.session_state.conversation = get_conversation_chain(retriever)
                        st.success("Documents processed successfully!")

    # Display chat messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Handle user input
    user_input = st.chat_input("Ask anything about your documents...")
    if user_input:
        if not st.session_state.conversation:
            st.error("Please upload documents first!")
        else:
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # Display user message
            with st.chat_message("user"):
                st.write(user_input)
            
            # Generate assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = st.session_state.conversation({"question": user_input})
                    answer = response["answer"]
                    
                    # Display assistant response
                    st.write(answer)
                    
                    # Add assistant response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})

if __name__ == "__main__":
    main()