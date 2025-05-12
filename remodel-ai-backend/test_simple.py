import requests
import json
BASE_URL = "http://localhost:8000"
# Start a conversation about kitchen remodel
response1 = requests.post(f"{BASE_URL}/api/v1/chat/", json={
    "content": "I want to remodel a 200 sq ft kitchen in San Diego",
    "role": "user"
})
if response1.status_code != 200:
    print(f"Error: {response1.status_code}")
    print(response1.text)
    exit(1)
data1 = response1.json()
session_id = data1.get("session_id")
print("Q: I want to remodel a 200 sq ft kitchen in San Diego")
print(f"A: {data1['message'][:150]}...")
print(f"Session ID: {session_id}")
print()
# Ask about timeline
response2 = requests.post(f"{BASE_URL}/api/v1/chat/", json={
    "content": "How long would that take?",
    "role": "user",
    "session_id": session_id
})
data2 = response2.json()
print("Q: How long would that take?")
print(f"A: {data2['message'][:150]}...")