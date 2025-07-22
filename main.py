"""
Terminal interface for testing the crisis response system.
Supports both local and online handlers.
"""
import logging
import os
from src.handlers.local_handler import LocalHandler
from src.handlers.online_handler import OnlineHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crisis_response.log'),
        logging.StreamHandler()
    ]
)

def choose_handler():
    """Let user choose between local and online handler"""
    print("Choose your handler:")
    print("1. Local (Ollama - gemma3n)")
    print("2. Online (Google Gemini)")
    
    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            try:
                return LocalHandler("gemma3n:latest")
            except Exception as e:
                print(f"❌ Failed to initialize local handler: {e}")
                print("Make sure Ollama is running and you have the model:")
                print("  ollama pull gemma3n")
                continue
                
        elif choice == "2":
            api_key = input("Enter your GEMINI_API_KEY (or press Enter to use env var): ").strip()
            if not api_key:
                api_key = os.getenv("GEMINI_API_KEY")
            
            if not api_key:
                print("❌ API key required for online mode")
                continue
                
            try:
                return OnlineHandler("gemini-2.5-flash", api_key)
            except Exception as e:
                print(f"❌ Failed to initialize online handler: {e}")
                continue
        else:
            print("Invalid choice. Please enter 1 or 2.")

def main():
    print("🚨 Crisis Response AI Toolkit - Terminal Mode")
    print("=" * 50)
    
    # Choose and initialize handler
    handler = choose_handler()
    print(f"✅ {handler.__class__.__name__} initialized successfully!")
    
    print("\nType 'quit', 'exit' or 'bye' to exit")
    print("Try saying something like: 'I've fallen and can't get up'")
    print("=" * 50)
    print("\nYou can start chatting now...\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye! Stay safe!")
                break
                
            if not user_input:
                continue
            
            # Process the message (same interface for both handlers!)
            response, tools_used = handler.handle_message(user_input)
            
            # Display results
            print(f"\nAssistant: {response}")
            
            if tools_used:
                print("\n🔧 Emergency Tools Executed:")
                for tool in tools_used:
                    result = tool['result']
                    status_icon = "✅" if result.get('status') == 'success' else "❌"
                    print(f"  {status_icon} {tool['tool']}: {result.get('message', 'No message')}")
                    
                    if 'incident_id' in result:
                        print(f"     📝 Incident ID: {result['incident_id']}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            logging.error(f"Unexpected error: {e}", exc_info=True)

if __name__ == "__main__":
    main()