import streamlit as st
import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

def handle_online_mode(gemini_api_key, selected_model, prompt):
    """
    Handles the chat logic for online models using Google AI Studio with streaming.
    """
    api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Please enter your GEMINI_API_KEY in the sidebar or set it in a .env file to chat.")
        st.stop()
    
    try:
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(selected_model)

        chat_history = [
            {"role": "model" if msg["role"] == "assistant" else "user", "parts": [msg["content"]]}
            for msg in st.session_state.messages[:-1] 
        ]
        logger.info(f"Chat history sent to model: {chat_history}")

        with st.spinner("Thinking..."):
            response_placeholder = st.empty()
            full_response = ""
            
            # Stream the response from the model
            response_stream = model.generate_content(
                chat_history + [{"role": "user", "parts": [prompt]}],
                stream=True
            )
            
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)

        if full_response:
            logger.info(f"Model response received: {full_response}")
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        else:
            logger.warning("Model did not return any text.")
            st.warning("The model did not return any text. Please check the safety settings in your Google AI Studio dashboard.")
            st.session_state.messages.pop()

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        st.error(f"An error occurred: {e}")
        st.session_state.messages.pop()
