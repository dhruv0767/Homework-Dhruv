import streamlit as st
from openai import OpenAI
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chromadb
from chromadb.utils import embedding_functions
import PyPDF2
import os

client = OpenAI(api_key=st.secrets["openai_api_key"])

def run():
    st.subheader("Dhruv's Question Answering Chatbot")

    def create_chromadb_collection(pdf_files):
        if 'HW4' not in st.session_state:
            try:
                chroma_client = chromadb.PersistentClient(path="./chroma_db")
                openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=st.secrets["openai_api_key"],
                    model_name="text-embedding-ada-002"
                )
                st.session_state.HW4 = chroma_client.get_or_create_collection(
                    name="HW4_collection",
                    embedding_function=openai_ef
                )
                
                for file in pdf_files:
                    try:
                        pdf_text = ""
                        pdf_reader = PyPDF2.PdfReader(file)
                        for page in pdf_reader.pages:
                            pdf_text += page.extract_text()
                        
                        st.session_state.HW4.add(
                            documents=[pdf_text],
                            metadatas=[{"filename": file.name}],
                            ids=[file.name]
                        )
                    except Exception as e:
                        st.error(f"Error processing {file.name}: {e}")
                
                st.success("ChromaDB has been created and documents have been embedded!")
            except Exception as e:
                st.error(f"Error creating ChromaDB collection: {e}")

    def get_relevant_context(query):
        if 'HW4' in st.session_state:
            try:
                results = st.session_state.HW4.query(
                    query_texts=[query],
                    n_results=5,
                    include=["documents", "metadatas"]
                )
                
                context = ""
                for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                    new_context = f"From document '{metadata['filename']}':\n{doc}\n\n"
                    context += new_context
                
                return context
            except Exception as e:
                st.error(f"Error retrieving context: {e}")
                return ""
        return ""

    def truncate_context(context, max_tokens=3000):
        tokens = context.split()
        if len(tokens) > max_tokens:
            return " ".join(tokens[:max_tokens])
        return context

    def generate_response(messages):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"

    st.title("Understanding your courses!")

    pdf_files = st.file_uploader("Upload your PDF files", accept_multiple_files=True, type=["pdf"])

    if st.button("Create/Update ChromaDB") and pdf_files:
        create_chromadb_collection(pdf_files)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What questions do you have?"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        context = get_relevant_context(prompt)
        truncated_context = truncate_context(context)

        system_message = "You are a helpful assistant that answers questions about courses based on the provided context. If the answer is not in the context, say you don't have that information."
        user_message = f"Context: {truncated_context}\n\nQuestion: {prompt}"

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        response = generate_response(messages)

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    run()