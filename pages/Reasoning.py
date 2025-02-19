import streamlit as st
from together import Together
from components.login import require_auth

def main_content():
    # Configure page
    st.set_page_config(page_title="Reasoning", page_icon="🤖")

    # Initialize Together client with API key from secrets
    client = Together(api_key=st.secrets["TOGETHER_API_KEY"])

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.title("Reasoning Assistant 🤖")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to discuss?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Prepare messages for API
        messages = [{"role": m["role"], "content": m["content"]} 
                   for m in st.session_state.messages]
        
        # Display assistant response with streaming
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                response = client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-R1",
                    messages=messages,
                    max_tokens=None,
                    temperature=0.6,
                    top_p=0.95,
                    top_k=50,
                    repetition_penalty=1,
                    stop=["<｜end▁of▁sentence｜>"],
                    stream=True
                )
                
                # Process streaming response
                for token in response:
                    if hasattr(token, 'choices'):
                        content = token.choices[0].delta.content
                        full_response += content
                        message_placeholder.write(full_response + "▌")
                
                # Update final response
                message_placeholder.write(full_response)
                
                # Add assistant response to chat history
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

require_auth(main_content)
