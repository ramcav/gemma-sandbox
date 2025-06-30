# gemma-sandbox
Function Calling Sandbox for Gemma Models (GSoC - DeepMind project)

## Overview

In this project I attempt to create a sandbox environment for testing function calling capabilities of Gemma models using MCP servers and a local gemma instance running with Ollama. The idea is for this porject to be built very moudularly so that it can be extended to support other models and use cases in the future.

The mian use case I want to focus on is "Crisis Response" where the model can be used to assist in decision making during crisis situations by calling functions that provide real-time data and insights, and also serving as a **Universal Translator for Intent**, allowing the model to understand and translate user intents into actionable functions.

## Visualizing the Sandbox's Utility

### Scenario 1

User: A volunteer coordinator in Valencia during the La DANA storm. She's not a programmer or an emergency management expert. She's just a person trying to help.
Her Problem: She gets a frantic message: "My street is flooding near the Mestalla stadium, and my elderly grandmother is with me. She only speaks Ukrainian. Where is the closest dry shelter, and can you give me evacuation instructions in her language?"
Without your sandbox, she would have to:
Open Google Maps to find shelters.
Try to figure out which ones are designated for flood response.
Open Google Translate.
Copy and paste instructions back and forth.
Potentially call an emergency number and wait on hold.
With your Gemma Function-Calling Sandbox, she does one thing:
She types that entire message into a simple text box in your app and clicks "Execute."
What the Sandbox Visualizes for Her:
The sandbox provides a clear, step-by-step log of what the AI is doing on her behalf:
▶️ **User Request Received:** "Find nearest shelter to Mestalla stadium and translate instructions to Ukrainian."
🧠 **Gemma Analyzing:** Okay, I need to perform two actions: find a location and translate a message.
⚙️ **Action 1 Triggered:** Calling toolfind_emergency_shelter()with parameters(location="Mestalla Stadium", disaster_type="flood").
✅ **Action 1 Result:** Shelter found at "Centro de Convenciones, Avinguda de les Fires, 1".
⚙️ **Action 2 Triggered:** Calling tooltranslate_text()with parameters(text="Please evacuate to the Centro de Convenciones...", target_language="uk").
✅ **Action 2 Result:** "Будь ласка, евакуюйтеся до Centro de Convenciones..."
🏁 **Final Output Presented:**
Nearest Shelter: Centro de Convenciones, Avinguda de les Fires, 1. [Show on map]
Instructions in Ukrainian: Будь ласка, евакуюйтеся до...
The Utility: She went from a complex, multi-step problem to a single-step solution. The sandbox became her personal, instant dispatcher.


## Features
- Simple streamlit UI (for now) that lets you select the model used (either locally or through Google AI Studio).
- Chat component that allows you to interact with the model.
- Our own collapsable menu that lets us add custom functions that can be called by the model (maybe they can live in a local MCP server) and MCP servers (like in Claude Desktop) easy to add with a add MCP server button and we are able to manage the tool access there.
- Selection menu to decide what MCP servers the model can have access during the session. If any service needs an API key, it can be added in the settings menu.
- Easy way to track the model's function calls, responses and reasoning.

