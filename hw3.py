import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import requests
import toml
import os
from bs4 import BeautifulSoup

# Load API keys from secrets.toml in .streamlit folder
secrets_path = os.path.join(".streamlit", "secrets.toml")
secrets = toml.load(secrets_path)

# Configure Gemini
genai.configure(api_key=secrets['gemini_api_key'])

def fetch_url_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        return ' '.join(text.split())[:1000]
    except Exception as e:
        return f"Error fetching URL: {str(e)}"

def generate_response(llm_model, context, question, conversation_memory):
    if llm_model.startswith("OpenAI"):
        model = "gpt-3.5-turbo" if llm_model == "OpenAI GPT-3.5" else "gpt-4"
        client = OpenAI(api_key=secrets['openai_api_key'])
        try:
            messages = [
                {"role": "system", "content": f"You are a helpful assistant. Use the following context to answer questions: {context}"},
                *conversation_memory,
                {"role": "user", "content": question}
            ]

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )

            message_placeholder = st.empty()
            full_response = ""

            for chunk in response:
                full_response += chunk.choices[0].delta.content or ""
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            return full_response

        except Exception as e:
            st.error(f"Error generating answer: {str(e)}")
            return None

    elif llm_model == "Google Gemini":
        try:
            model = genai.GenerativeModel('gemini-pro')
            chat = model.start_chat(history=[])
            for message in conversation_memory:
                chat.send_message(message['content'])
            response = chat.send_message(f"{context}\n\n{question}")
            return response.text
        except Exception as e:
            st.error(f"Error generating answer: {str(e)}")
            return None

    elif llm_model == "Cohere Command-R":
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {secrets['cohere_api_key']}"
        }
        conversation_history = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_memory])
        data = {
            "prompt": f"{context}\n\n{conversation_history}\n\nHuman: {question}\n\nAssistant:",
            "max_tokens": 2048,
            "temperature": 0.5,
            "p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "model": "command"
        }
        response = requests.post("https://api.cohere.ai/v1/generate", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["generations"][0]["text"]
        else:
            st.error(f"Error generating answer: {response.text}")
            return None

def run():
    st.subheader("Dhruv's Question Answering Chatbot")

    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    if 'waiting_for_more_info' not in st.session_state:
        st.session_state['waiting_for_more_info'] = False

    st.sidebar.subheader("Select LLM Model")
    llm_model = st.sidebar.selectbox("Choose LLM to use", ["OpenAI GPT-3.5", "OpenAI GPT-4", "Google Gemini", "Cohere Command-R"])

    url1 = st.sidebar.text_input("Enter the first URL")
    url2 = st.sidebar.text_input("Enter the second URL")

    st.sidebar.subheader("Conversation Memory Settings")
    conversation_memory_type = st.sidebar.radio("Memory Type", ("Buffer of 5 questions", "Conversation Summary", "Buffer of 5,000 tokens"))

    question = st.text_input("Ask a question about the URLs:")

    if question:
        st.session_state['messages'].append({"role": "user", "content": question})

        context = ""
        if url1:
            context += f"URL1 content: {fetch_url_content(url1)} "
        if url2:
            context += f"URL2 content: {fetch_url_content(url2)} "

        # Implement conversation memory
        if conversation_memory_type == "Buffer of 5 questions":
            conversation_memory = st.session_state['messages'][-10:]  # Last 5 Q&A pairs
        elif conversation_memory_type == "Conversation Summary":
            conversation_memory = st.session_state['messages'][-1:]
        else:  # Buffer of 5,000 tokens
            conversation_memory = []
            token_count = 0
            for message in reversed(st.session_state['messages']):
                token_count += len(message['content'].split())
                if token_count > 5000:
                    break
                conversation_memory.insert(0, message)

        response = generate_response(llm_model, context, question, conversation_memory)
        if response:
            st.markdown("## Answer")
            st.markdown(response)
            st.session_state['messages'].append({"role": "assistant", "content": response})
            st.session_state['waiting_for_more_info'] = True

    if st.session_state['waiting_for_more_info']:
        more_info = st.radio("Do you want more information?", ("Yes", "No"))
        if st.button("Submit"):
            if more_info == "Yes":
                follow_up_question = "Please provide more detailed information about the previous answer."
                st.session_state['messages'].append({"role": "user", "content": follow_up_question})
                
                context = ""
                if url1:
                    context += f"URL1 content: {fetch_url_content(url1)} "
                if url2:
                    context += f"URL2 content: {fetch_url_content(url2)} "
                
                # Use the same conversation memory logic for follow-up questions
                if conversation_memory_type == "Buffer of 5 questions":
                    conversation_memory = st.session_state['messages'][-10:]
                elif conversation_memory_type == "Conversation Summary":
                    conversation_memory = st.session_state['messages'][-1:]
                else:  # Buffer of 5,000 tokens
                    conversation_memory = []
                    token_count = 0
                    for message in reversed(st.session_state['messages']):
                        token_count += len(message['content'].split())
                        if token_count > 5000:
                            break
                        conversation_memory.insert(0, message)
                
                response = generate_response(llm_model, context, follow_up_question, conversation_memory)
                if response:
                    st.markdown("## Additional Information")
                    st.markdown(response)
                    st.session_state['messages'].append({"role": "assistant", "content": response})
            else:
                st.write("What question do you want me to answer?")
            st.session_state['waiting_for_more_info'] = False

    st.subheader("Conversation History")
    for message in st.session_state['messages']:
        with st.expander(message["role"]):
            st.markdown(message["content"])