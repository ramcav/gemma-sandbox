# Gemma Function-Calling Sandbox


In this project I attempt to create a sandbox environment for testing function calling capabilities of Gemma models using MCP servers and a local gemma instance running with Ollama. The idea is for this project to be built very moudularly so that it can be extended to support other models and use cases in the future.

The main use case I want to focus on is "Crisis Response" where the model can be used to assist in decision making during crisis situations by calling functions that provide real-time data and insights, and also serving as a **Universal Translator for Intent**, allowing the model to understand and translate user intents into actionable functions.


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
