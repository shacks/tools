import streamlit as st
import requests
import json

# Configure page
st.set_page_config(page_title="Chat with Perplexity AI", page_icon="🤖", layout="wide")

# Sidebar controls
with st.sidebar:
    st.header("Model Settings")
    
    # Model selection
    MODEL_OPTIONS = {
        "Sonar Reasoning Pro (127k tokens)": "sonar-reasoning-pro",
        "Sonar Reasoning (127k tokens)": "sonar-reasoning",
        "Sonar Pro (200k tokens)": "sonar-pro",
        "Sonar (127k tokens)": "sonar"
    }
    
    selected_model = st.selectbox(
        "Select Model",
        options=list(MODEL_OPTIONS.keys()),
        index=0
    )
    
    # Token slider based on model
    max_possible_tokens = 200000 if "pro" in MODEL_OPTIONS[selected_model] else 127000
    token_count = st.slider(
        "Max Tokens",
        min_value=100,
        max_value=max_possible_tokens,
        value=1000,
        step=100,
        help=f"Maximum tokens for this model: {max_possible_tokens}"
    )
    
    # Temperature control
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.1,
        help="Higher values make output more random, lower values more deterministic"
    )

st.title("Chat with Perplexity AI")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What's on your mind?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare API request
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": MODEL_OPTIONS[selected_model],
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            },
            *[{"role": msg["role"], "content": msg["content"]} 
              for msg in st.session_state.messages]
        ],
        "max_tokens": token_count,
        "temperature": temperature,
        "top_p": 0.9,
        "stream": False,
        "frequency_penalty": 1
    }
    
    headers = {
        "Authorization": f"Bearer {st.secrets['PERPLEXITY_API_KEY']}",
        "Content-Type": "application/json"
    }

    # Make API request
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status()
                response_data = response.json()
                
                # Handle response
                assistant_response = response_data["choices"][0]["message"]["content"]
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                st.markdown(assistant_response)
                
                # Display citations if available
                if "citations" in response_data and response_data["citations"]:
                    with st.expander("Sources"):
                        for citation in response_data["citations"]:
                            st.write(citation)
                            
            except requests.exceptions.HTTPError as http_err:
                st.error(f"HTTP Error: {http_err}")
                st.error(f"Response: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")