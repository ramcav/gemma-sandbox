# Crisis Response AI Toolkit

An AI-powered crisis response toolkit designed to run locally using Gemma 3n and handle real-world emergency scenarios using function-calling.

## Overview

This project focuses on privacy-first, offline-capable crisis detection and response. The core components are lightweight, modular, and interpretable, making it easy for developers to extend and integrate into their own crisis-specific agents or assistants.

**Key Features:**
- 🏠 **Local-first**: Runs entirely offline using Ollama and Gemma 3n
- 🚨 **Crisis Detection**: Automatically detects emergency situations from natural language
- 🔧 **Function Calling**: Executes appropriate emergency response tools
- 🔒 **Privacy-focused**: No data leaves your device
- 🧩 **Modular**: Easy to extend with additional tools and handlers

## Quick Start

### Prerequisites

- [Ollama](https://ollama.ai/) installed and running
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rorosaga/gemma-sandbox.git
   cd gemma-sandbox
   ```

2. **Install dependencies with uv:**
   ```bash
   uv sync
   ```

3. **Pull the Gemma model:**
   ```bash
   ollama pull gemma3n
   ```

4. **Run the toolkit:**
   ```bash
   uv run main.py
   ```

### Usage

Once running, you can test the crisis detection by typing messages like:
- "I've fallen and can't get up"
- "Help me, I'm having chest pain" 
- "Emergency! I need assistance"
- "Just saying hello" (normal conversation)

The toolkit will detect crisis situations and automatically execute appropriate emergency response tools.
