from pinecone import Pinecone
import os
from dotenv import load_dotenv
load_dotenv()
# Initialize Pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index(os.getenv('PINECONE_INDEX'))
# Get index stats
stats = index.describe_index_stats()
print(f"Total vectors: {stats.total_vector_count}")
print(f"Dimensions: {stats.dimension}")
# Test query
test_vector = [0.1] * 1536  # Dummy vector
results = index.query(vector=test_vector, top_k=1, include_metadata=True)
if results['matches']:
    print(f"Test query returned {len(results['matches'])} results")
    print(f"Sample metadata: {results['matches'][0]['metadata']}")
else:
    print("No results found - index may be empty")