print("Start of script")
import sys
sys.stdout.flush()

try:
    import os
    print("Imported os")
    import dotenv
    print("Imported dotenv")
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    print("Imported langchain_google_genai")
except Exception as e:
    print(f"Import Error: {e}")
    sys.exit(1)

dotenv.load_dotenv()

def test_embedding():
    print("Initializing Embeddings...")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        print("Embedding a single string...")
        vector = embeddings.embed_query("Hello, world!")
        print(f"Success! Vector length: {len(vector)}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_embedding()
