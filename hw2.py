import streamlit as st
import requests
from bs4 import BeautifulSoup

def run():
    st.title("URL Content Summarizer")

    # Input field for the URL
    url = st.text_input("Enter the URL you want to summarize:")

    # Sidebar for summary type
    summary_type = st.sidebar.selectbox(
        "Select the type of summary:",
        ("Short Summary", "Detailed Summary", "Bullet Points")
    )

    # Language selection
    language = st.sidebar.selectbox(
        "Select the output language:",
        ("English", "French", "Spanish")
    )

    # LLM selection (move it outside of if-block)
    llm = st.sidebar.selectbox(
        "Select the LLM to use:",
        ("OpenAI GPT-3.5", "Anthropic Claude", "Cohere Command")
    )

    # Use advanced model checkbox (also move it outside of if-block)
    use_advanced_model = st.sidebar.checkbox("Use Advanced Model")

    # Initialize API key variables
    openai_api_key = None
    anthropic_api_key = None
    cohere_api_key = None

    # API Key Inputs based on LLM selection
    if llm == "OpenAI GPT-3.5":
        openai_api_key = st.sidebar.text_input("Enter your OpenAI API key:", type="password")
    elif llm == "Anthropic Claude":
        anthropic_api_key = st.sidebar.text_input("Enter your Anthropic API key:", type="password")
    elif llm == "Cohere Command":
        cohere_api_key = st.sidebar.text_input("Enter your Cohere API key:", type="password")

    def read_url_content(url):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup.get_text()
        except requests.RequestException as e:
            st.error(f"Error reading {url}: {e}")
            return None

    def validate_openai_key(api_key):
        try:
            import openai
            openai.api_key = api_key
            openai.Engine.list()
            return True
        except Exception as e:
            st.error(f"OpenAI API key validation failed: {e}")
            return False

    def validate_anthropic_key(api_key):
        try:
            import anthropic
            client = anthropic.Client(api_key)
            client.completions.create(prompt="", max_tokens_to_sample=5)
            return True
        except Exception as e:
            st.error(f"Anthropic API key validation failed: {e}")
            return False

    def validate_cohere_key(api_key):
        try:
            import cohere
            co = cohere.Client(api_key)
            co.generate(prompt="", max_tokens=5)
            return True
        except Exception as e:
            st.error(f"Cohere API key validation failed: {e}")
            return False

    def generate_summary_openai(content, summary_type, language, advanced):
        import openai
        openai.api_key = openai_api_key
        model = "text-davinci-003" if advanced else "text-curie-001"
        prompt = f"Please provide a {summary_type.lower()} of the following content in {language}:\n\n{content}"
        response = openai.Completion.create(
            engine=model,
            prompt=prompt,
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].text.strip()

    def generate_summary_anthropic(content, summary_type, language, advanced):
        import anthropic
        client = anthropic.Client(anthropic_api_key)
        model = "claude-v1" if advanced else "claude-instant-v1"
        prompt = f"{anthropic.HUMAN_PROMPT} Please provide a {summary_type.lower()} of the following content in {language}:\n\n{content}{anthropic.AI_PROMPT}"
        response = client.completions.create(
            model=model,
            prompt=prompt,
            max_tokens_to_sample=150,
        )
        return response.completion.strip()

    def generate_summary_cohere(content, summary_type, language, advanced):
        import cohere
        co = cohere.Client(cohere_api_key)
        model = "command-xlarge-nightly" if advanced else "command-medium-nightly"
        prompt = f"Please provide a {summary_type.lower()} of the following content in {language}:\n\n{content}"
        response = co.generate(
            model=model,
            prompt=prompt,
            max_tokens=150,
            temperature=0.7,
        )
        return response.generations[0].text.strip()

    if url:
        content = read_url_content(url)
        if content:
            st.write("Original Content (First 500 characters):")
            st.write(content[:500] + "...")

            # Initialize summary
            summary = None

            # Generate the summary based on LLM selection
            if llm == "OpenAI GPT-3.5":
                if openai_api_key and validate_openai_key(openai_api_key):
                    summary = generate_summary_openai(content, summary_type, language, use_advanced_model)
            elif llm == "Anthropic Claude":
                if anthropic_api_key and validate_anthropic_key(anthropic_api_key):
                    summary = generate_summary_anthropic(content, summary_type, language, use_advanced_model)
            elif llm == "Cohere Command":
                if cohere_api_key and validate_cohere_key(cohere_api_key):
                    summary = generate_summary_cohere(content, summary_type, language, use_advanced_model)

            # Display the summary if it was generated
            if summary:
                st.subheader("Summary:")
                st.write(summary)
            else:
                st.error("No summary was generated. Please check your API keys or input.")