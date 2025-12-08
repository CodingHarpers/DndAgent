import os
import google.generativeai as genai
import sys

print(f"Python Version: {sys.version}")
print(f"GenAI Version: {genai.__version__}")

key = os.getenv("GOOGLE_API_KEY", "")
print(f"Key loaded: {'Yes' if key else 'No'}")
print(f"Key length: {len(key)}")
print(f"Key starts with: {key[:4]}...")

if not key or "your_key" in key:
    print("❌ ERROR: Invalid API Key found.")
    exit(1)

genai.configure(api_key=key)

try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Hello, can you hear me?")
    print(f"✅ API Test Success: {response.text}")
except Exception as e:
    print(f"❌ API Test Failed: {e}")
