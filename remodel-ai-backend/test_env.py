import os
print("Environment variables check:")
print(f"OPENAI_API_KEY exists: {'OPENAI_API_KEY' in os.environ}")
print(f"PINECONE_API_KEY exists: {'PINECONE_API_KEY' in os.environ}")
print(f"PINECONE_INDEX exists: {'PINECONE_INDEX' in os.environ}")
print(f"All env vars: {list(os.environ.keys())}")
