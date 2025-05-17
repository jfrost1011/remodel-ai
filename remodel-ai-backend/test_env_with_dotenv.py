import os
from dotenv import load_dotenv
# Load .env file
load_dotenv()
print("Environment variables check after loading .env:")
print(f"OPENAI_API_KEY exists: {'OPENAI_API_KEY' in os.environ}")
print(f"PINECONE_API_KEY exists: {'PINECONE_API_KEY' in os.environ}")
print(f"PINECONE_INDEX exists: {'PINECONE_INDEX' in os.environ}")
