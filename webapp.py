import streamlit as st
import requests

hide_streamlit_style = """
            <style>
            #MainMenu {visibility : hidden;}
                footer {visibility : hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html = True)

st.markdown("<h1 style='text-align: center; color: red;'>Test Case Generation</a></h1>", unsafe_allow_html = True)

def main():
    file_uploaded = st.file_uploader('Upload an SRS Document...', type='txt')
    
    if file_uploaded is not None:
        srs_document = file_uploaded.read().decode("utf-8")
        test_cases = generate_test_cases_from_srs(srs_document)
        
        st.write("Generated Test Cases:")
        st.write(test_cases)

def generate_test_cases_from_srs(srs_document):
    # Define the API endpoint URL
    api_url = "http://localhost:8000/generate_use_cases"  # Update this URL if your FastAPI server is running on a different address or port
    
    # Send the SRS document to the FastAPI endpoint
    files = {'file': ('srs_document.txt', srs_document, 'text/plain')}
    response = requests.post(api_url, files=files)
    
    # Check if the request was successful
    if response.status_code == 200:
        result = response.json()
        return result.get("use_cases", "No use cases generated.")
    else:
        return "Failed to generate use cases."

if __name__ == '__main__':
    main()
