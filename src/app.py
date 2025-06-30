import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from online_handler import handle_online_mode
from local_handler import handle_local_mode
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="Gemma Function-Calling Sandbox",
    page_icon="🤖",
    layout="wide"
)

# --- Model Definitions ---
ONLINE_MODELS = {
    "GEMINI_2.5": ["gemini-2.5-pro", "gemini-2.5-flash"],
    "GEMINI_2.0": ["gemini-2.0-flash", "gemini-2.0-flash-lite"],
    "GEMMA": [
        "gemma-3n-e4b-it", "gemma-3-1b-it", "gemma-3-4b-it",
        "gemma-3-12b-it", "gemma-3-27b-it"
    ],
    "OTHER": ["learnlm-2.0-flash-experimental"]
}

# Flatten the dictionary for the selectbox, formatting the options
online_model_options = [
    f"{category} / {model}"
    for category, models in ONLINE_MODELS.items()
    for model in models
]

LOCAL_MODELS = ["gemma3n:latest"]


# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Sandbox Configuration")
    st.write("---")

    # --- Model Configuration ---
    st.header("Model Configuration")
    run_local = st.toggle("Run Local", value=False)
    st.write("---")

    selected_model = None
    if run_local:
        st.subheader("Local Model (Ollama)")
        selected_model = st.selectbox(
            "Select a local model",
            LOCAL_MODELS
        )
    else:
        st.subheader("Online Model (Google AI Studio)")
        gemini_api_key = st.text_input(
            "GEMINI_API_KEY",
            type="password",
            help="Paste your Google AI Studio API Key here.",
            value=os.getenv("GEMINI_API_KEY", "")
        )
        
        # Extract the model name from the formatted string
        formatted_model = st.selectbox(
            "Select an online model",
            online_model_options
        )
        if formatted_model:
            selected_model = formatted_model.split(" / ")[1]


    # --- Context Management on Model Change ---
    # Use session state to track the active model and mode.
    # Initialize if it doesn't exist.
    if 'active_model_info' not in st.session_state:
        st.session_state.active_model_info = {
            "model": selected_model,
            "is_local": run_local
        }

    # Check if the model or mode has been changed by the user.
    model_changed = st.session_state.active_model_info["model"] != selected_model
    mode_changed = st.session_state.active_model_info["is_local"] != run_local

    if model_changed or mode_changed:
        st.warning("Model or mode has changed. For a clean slate, clear the chat history.")
        if st.button("Clear Chat History", use_container_width=True, key="clear_chat"):
            # Clear the messages
            st.session_state.messages = []
            # Update the tracker to the new model/mode
            st.session_state.active_model_info = {
                "model": selected_model,
                "is_local": run_local
            }
            logging.info("Chat history cleared due to model change.")
            # Rerun the app to reflect the cleared chat
            st.rerun()


    st.write("---")

    # Collapsible menu for Tools
    with st.expander("🛠️ Tool Management", expanded=True):
        st.write("Manage your custom functions and MCP servers.")
        # Placeholder for adding custom functions
        st.button("Add Custom Function", use_container_width=True)
        # Placeholder for adding MCP servers
        st.button("Add MCP Server", use_container_width=True)

    # Placeholder for selecting active tools
    st.multiselect(
        "Select Active Tools/MCPs",
        ["find_emergency_shelter", "translate_text"],
        default=["find_emergency_shelter", "translate_text"]
    )

    st.write("---")

    # # Collapsible menu for API Keys
    # with st.expander("🔑 API Keys"):
    #     st.text_input("Google AI Studio API Key", type="password", key="google_api_key")
    #     # You can add other API key inputs here as needed

# --- Main Chat Interface ---
st.title("Gemma Function-Calling Sandbox")
st.caption("A simple UI to test Gemma's function calling capabilities.")

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input from chat box
if prompt := st.chat_input("What can I help you with?"):
    # Add user message to chat history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display assistant's response
    with st.chat_message("assistant"):
        if not run_local:
            logging.info(f"Running in online mode with model: {selected_model}")
            handle_online_mode(gemini_api_key, selected_model, prompt)
        else:
            logging.info(f"Running in local mode with model: {selected_model}")
            handle_local_mode(selected_model, prompt)