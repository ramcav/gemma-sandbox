"""
Entry point for the Gemma MCP Sandbox application.
"""
import subprocess
import sys

if __name__ == "__main__":
    # Run the Streamlit app
    subprocess.run([sys.executable, "-m", "streamlit", "run", "src/main.py"] + sys.argv[1:])