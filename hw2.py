import streamlit as st
import requests
from bs4 import BeautifulSoup

def run():
    st.title("URL Content Summarizer")

    url = st.text_input("Enter the URL you want to summarize:")

    summary_type = st.sidebar.selectbox(
        "Select the type of summary:",
        ("Short Summary", "Detailed Summary", "Bullet Points")
    )

    language = st.sidebar.selectbox(
        "Select the output language:",
        ("English", "French", "Spanish")
    )

    llm = st.sidebar.selectbox(
        "Select the LLM to use:",
        ("OpenAI GPT-3.5", "Anthropic Claude", "Cohere Command")
    )

    use_advanced_model = st.sidebar.checkbox("Use Advanced Model")

    def read_url_content(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup.get_text()
        except requests.RequestException as e:
            st.error(f"Error reading {url}: {e}")
            return None

    def generate_summary_openai(content, summary_type, language, advanced):
        import openai
        openai.api_key = st.secrets["openai_api_key"]
        model = "gpt-3.5-turbo" if advanced else "gpt-3.5-turbo"
        prompt = f"Please provide a {summary_type.lower()} of the following content in {language}:\n\n{content}"
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"Error with OpenAI API: {e}")
            return None

    def generate_summary_anthropic(content, summary_type, language, advanced):
        from anthropic import Anthropic
        client = Anthropic(api_key=st.secrets["anthropic_api_key"])
        model = "claude-2" if advanced else "claude-instant-1"
        prompt = f"Human: Please provide a {summary_type.lower()} of the following content in {language}:\n\n{content}\n\nAssistant:"
        try:
            response = client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens_to_sample=300,
            )
            return response.completion.strip()
        except Exception as e:
            st.error(f"Error with Anthropic API: {e}")
            return None

    def generate_summary_cohere(content, summary_type, language, advanced):
        import cohere
        co = cohere.Client(st.secrets["cohere_api_key"])
        model = "command"
        prompt = f"Please provide a {summary_type.lower()} of the following content in {language}:\n\n{content}"
        try:
            response = co.generate(
                model=model,
                prompt=prompt,
                max_tokens=300,
                temperature=0.7,
            )
            return response.generations[0].text.strip()
        except Exception as e:
            st.error(f"Error with Cohere API: {e}")
            return None

    if url:
        content = read_url_content(url)
        if content:
            st.write("Original Content (First 500 characters):")
            st.write(content[:500] + "...")

            summary = None

            if llm == "OpenAI GPT-3.5":
                summary = generate_summary_openai(content, summary_type, language, use_advanced_model)
            elif llm == "Anthropic Claude":
                summary = generate_summary_anthropic(content, summary_type, language, use_advanced_model)
            elif llm == "Cohere Command":
                summary = generate_summary_cohere(content, summary_type, language, use_advanced_model)

            if summary:
                st.subheader("Summary:")
                st.write(summary)
            else:
                st.error("No summary was generated. Please check the API configuration or try again.")

if __name__ == "__main__":
    run()