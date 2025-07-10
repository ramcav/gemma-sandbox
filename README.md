# Gemma Function-Calling Sandbox


A sandbox environment for testing the function-calling capabilities of local and online Gemma models. This project serves as a **Universal Translator for Intent**, transforming natural language requests into actionable, programmatic functions.

## Features

-   🔄 **Dual Model Support:** Seamlessly switch between local models running via Ollama and powerful online models from Google AI Studio.
-   🛠️ **Dynamic Tool Management:** Easily add and manage custom functions and MCP (Model-Context-Protocol) servers on the fly.
-   🎛️ **Granular Tool Control:** A multi-select menu allows you to grant the model access to specific tools for a given session.
-   🔍 **Transparent Execution:** Clearly track the model's reasoning, function calls, and responses in a user-friendly chat interface.
-   ✨ **Simple & Extensible UI:** Built with Streamlit for rapid iteration, providing a clear view of the model's interactions.

## Visualizing the Sandbox's Utility

This sandbox turns complex, multi-step problems into single-step solutions, acting as a personal, instant dispatcher.

### Scenario

A volunteer coordinator during a storm receives a frantic message: *"My street is flooding near the Mestalla stadium, and my elderly grandmother is with me. She only speaks Ukrainian. Where is the closest dry shelter, and can you give me evacuation instructions in her language?"*

Instead of juggling multiple apps, she types the message into the sandbox. The UI provides a clear, step-by-step log as the AI works:

1.  ▶️ **User Request Received:** Find the nearest shelter and translate instructions to Ukrainian.
2.  🧠 **Gemma Analyzing:** I need to find a location and then translate a message.
3.  ⚙️ **Action 1 Triggered:** Calling `find_emergency_shelter(location="Mestalla Stadium", disaster_type="flood")`.
4.  ✅ **Action 1 Result:** Shelter found at "Centro de Convenciones".
5.  ⚙️ **Action 2 Triggered:** Calling `translate_text(text="Please evacuate to...", target_language="uk")`.
6.  ✅ **Action 2 Result:** "Будь ласка, евакуюйтеся до..."
7.  🏁 **Final Output Presented:** The nearest shelter's address and the evacuation instructions, perfectly translated.
