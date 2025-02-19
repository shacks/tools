import streamlit as st
from PyPDF2 import PdfReader
import io

google_button = st.button("Google Login")

if google_button:
    st.login(provider="google")


st.title("PDF Text Extractor")

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

# Password input
password = st.text_input("Enter PDF password (if encrypted)", type="password")

if uploaded_file is not None:
    try:
        # Read PDF content
        pdf_bytes = io.BytesIO(uploaded_file.getvalue())
        reader = PdfReader(pdf_bytes)
        
        if reader.is_encrypted:
            st.info("PDF is encrypted. Attempting to decrypt...")
            if reader.decrypt(password):
                st.success("PDF decrypted successfully.")
            else:
                st.error("Incorrect password or unable to decrypt the PDF.")
                st.stop()
        else:
            st.info("PDF is not encrypted.")

        # Extract text using PyPDF2
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        # Display extracted text
        st.subheader("Extracted Text")
        st.text_area("", text, height=300)

        # Download button
        st.download_button(
            label="Download extracted text",
            data=text,
            file_name="extracted_text.txt",
            mime="text/plain"
        )

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
