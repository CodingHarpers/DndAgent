import sys
import os
# Ensure app modules can be imported if running directly
try:
    from app.services.embeddings import get_single_embedding
    from app.services.generation import generation_client
except ImportError:
    # Fallback to verify path issues if run incorrectly
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
    from app.services.embeddings import get_single_embedding
    from app.services.generation import generation_client

def check_api():
    print(f"Python: {sys.version}")
    
    # 1. Check Keys
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    print(f"OpenAI Key: {'✅ Present' if openai_key else '❌ Missing'}")
    print(f"Gemini Key: {'✅ Present' if gemini_key else '❌ Missing'}")
    
    if not openai_key or not gemini_key:
        print("⚠️ Warning: Missing keys may cause failures.")
        
    # 2. Check Embedding
    print("\n--- Testing OpenAI Embeddings ---")
    try:
        vector = get_single_embedding("Hello world")
        print(f"✅ Success! Vector dim: {len(vector)}")
        if len(vector) == 1536:
            print("✅ Dimension 1536 confirmed (text-embedding-3-small)")
        else:
            print(f"⚠️ Unexpected dimension: {len(vector)}")
    except Exception as e:
        print(f"❌ Embedding Failed: {e}")

    # 3. Check Generation
    print("\n--- Testing Gemini Generation ---")
    
    # Diagnostic: List models
    import google.generativeai as genai
    genai.configure(api_key=gemini_key)
    print("Available Models:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f" - {m.name}")
    except Exception as list_err:
        print(f"Error listing models: {list_err}")

    try:
        response = generation_client.generate_text(
            system_prompt="You are a test bot.",
            user_prompt="Say 'Function active'."
        )
        print(f"Response: {response}")
        if "active" in response.lower() or "function" in response.lower():
            print("✅ Generation confirmed functional")
        else:
            print("⚠️ Generation response checking (check manually above)")
    except Exception as e:
        print(f"❌ Generation Failed: {e}")

if __name__ == "__main__":
    check_api()
