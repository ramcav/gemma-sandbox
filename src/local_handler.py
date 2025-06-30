import streamlit as st
import ollama
import logging

logger = logging.getLogger(__name__)

def handle_local_mode(selected_model, prompt):
    """
    Handles the chat logic for local models using Ollama.
    """
    try:
        # Format messages for Ollama. The last message is the new prompt.
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in st.session_state.messages
        ]
        logger.info(f"Messages sent to Ollama: {messages}")

        # Use a Streamlit placeholder to stream the response
        with st.spinner("Thinking..."):
            response_placeholder = st.empty()
            full_response = ""
            # Stream the response from Ollama
            for chunk in ollama.chat(model=selected_model, messages=messages, stream=True):
                full_response += chunk['message']['content']
                response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)

        # Add the complete assistant response to the chat history
        logger.info(f"Ollama response received: {full_response}")
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        logger.error(f"An error occurred with Ollama: {e}", exc_info=True)
        st.error(f"An error occurred with Ollama: {e}")
        st.info("Please make sure Ollama is running and the model is available. You can pull the model with `ollama pull gemma3n`.")
        # Remove the last user message if an error occurs so they can try again
        st.session_state.messages.pop()
