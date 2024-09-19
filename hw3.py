import streamlit as st
import openai
import requests

def run():
    st.subheader("Dhruv's Question Answering Chatbot")

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    if 'waiting_for_more_info' not in st.session_state:
        st.session_state['waiting_for_more_info'] = False

    # Load API keys from secrets.toml
    chatgpt_key = st.secrets["openai_api_key"]
    anthropic_key = st.secrets["anthropic_api_key"]
    cohere_key = st.secrets["cohere_api_key"]

    # Sidebar: Model selection (LLMs)
    st.sidebar.subheader("Select LLM Model")
    llm_model = st.sidebar.selectbox("Choose LLM to use", ["OpenAI GPT-3.5", "OpenAI GPT-4", "Anthropic Claude-2", "Cohere Command-R"])

    # Sidebar: URLs input
    url1 = st.sidebar.text_input("Enter the first URL")
    url2 = st.sidebar.text_input("Enter the second URL")

    # Sidebar: Conversation memory selection
    st.sidebar.subheader("Conversation Memory Settings")
    conversation_memory = st.sidebar.radio("Memory Type", ("Buffer of 5 questions", "Conversation Summary", "Buffer of 5,000 tokens"))

    # Chatbot functionality
    if not st.session_state['waiting_for_more_info']:
        question = st.text_input("Ask a question about the URLs:")

        if question:
            st.session_state['messages'].append({"role": "user", "content": question})

            # Gather context from URLs
            context = ""
            if url1:
                context += f"URL1: {url1} "
            if url2:
                context += f"URL2: {url2} "

            # Select model to use based on sidebar input
            if llm_model == "OpenAI GPT-3.5" or llm_model == "OpenAI GPT-4":
                model = "gpt-3.5-turbo" if llm_model == "OpenAI GPT-3.5" else "gpt-4"
                openai.api_key = chatgpt_key
                try:
                    messages = [
                        {"role": "system", "content": context},
                        *st.session_state['messages']
                    ]

                    response = openai.chat.completions.create(
                        model=model,
                        messages=messages,
                        stream=True
                    )

                    message_placeholder = st.empty()
                    full_response = ""

                    for chunk in response:
                        full_response += chunk['choices'][0].get('delta', {}).get('content', '')
                        message_placeholder.markdown(full_response + "▌")
                    
                    message_placeholder.markdown(full_response)
                    st.session_state['messages'].append({"role": "assistant", "content": full_response})

                    # Set waiting_for_more_info to True after each response
                    st.session_state['waiting_for_more_info'] = True

                except Exception as e:
                    st.error(f"Error generating answer: {str(e)}")

            elif llm_model == "Anthropic Claude-2":
                # Implement Anthropic API call
                headers = {
                    "Content-Type": "application/json",
                    "x-api-key": anthropic_key
                }
                data = {
                    "prompt": context + "\n" + question,
                    "max_tokens": 2048,
                    "temperature": 0.5,
                    "top_p": 1,
                    "frequency_penalty": 0,
                    "presence_penalty": 0
                }
                response = requests.post("https://api.anthropic.com/v1/complete", headers=headers, json=data)
                if response.status_code == 200:
                    full_response = response.json()["completion"]
                    st.session_state['messages'].append({"role": "assistant", "content": full_response})
                    st.session_state['waiting_for_more_info'] = True
                else:
                    st.error(f"Error generating answer: {response.text}")

            elif llm_model == "Cohere Command-R":
                # Implement Cohere API call
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {cohere_key}"
                }
                data = {
                    "prompt": context + "\n" + question,
                    "max_tokens": 2048,
                    "temperature": 0.5,
                    "top_p": 1,
                    "frequency_penalty": 0,
                    "presence_penalty": 0
                }
                response = requests.post("https://api.cohere.ai/v1/generate", headers=headers, json=data)
                if response.status_code == 200:
                    full_response = response.json()["generations"][0]["text"]
                    st.session_state['messages'].append({"role": "assistant", "content": full_response})
                    st.session_state['waiting_for_more_info'] = True
                else:
                    st.error(f"Error generating answer: {response.text}")

    # Handle the follow-up question
    if st.session_state['waiting_for_more_info']:
        more_info = st.radio("Do you want more information?", ("Yes", "No"))
        if st.button("Submit"):
            if more_info == "Yes":
                st.session_state['messages'].append({"role": "user", "content": " Please provide more information."})
                # Repeat the API call process based on the selected model
            else:
                st.write("What question do you want me to answer?")
            st.session_state['waiting_for_more_info'] = False
            try:
                st.rerun()
            except AttributeError:
                st.rerun()

    # Display conversation history
    st.subheader("Conversation History")
    for message in st.session_state['messages']:
        with st.expander(message["role"]):
            st.markdown(message["content"])

if __name__ == "__main__":
    run()