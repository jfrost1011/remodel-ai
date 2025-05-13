import requests
import json
import time
BASE_URL = "http://localhost:8000"
def test_chat_conversation():
    """Test a full conversation flow"""
    print("Testing Chat Conversation Flow")
    print("=" * 50)
    # Start a conversation
    session_id = None
    # First message
    response = requests.post(f"{BASE_URL}/api/v1/chat/", json={
        "content": "I'm looking to remodel my kitchen in San Diego",
        "role": "user"
    })
    data = response.json()
    session_id = data["session_id"]
    print(f"User: I'm looking to remodel my kitchen in San Diego")
    print(f"Assistant: {data['message'][:150]}...")
    print()
    # Follow-up question
    response = requests.post(f"{BASE_URL}/api/v1/chat/", json={
        "content": "What about if I have a 200 square foot kitchen?",
        "role": "user",
        "session_id": session_id
    })
    data = response.json()
    print(f"User: What about if I have a 200 square foot kitchen?")
    print(f"Assistant: {data['message'][:150]}...")
    print()
    # Another follow-up
    response = requests.post(f"{BASE_URL}/api/v1/chat/", json={
        "content": "How long would that take?",
        "role": "user",
        "session_id": session_id
    })
    data = response.json()
    print(f"User: How long would that take?")
    print(f"Assistant: {data['message'][:150]}...")
    print()
    # Get conversation history
    response = requests.get(f"{BASE_URL}/api/v1/chat/sessions/{session_id}/history")
    history = response.json()
    print(f"\nConversation history: {len(history['history'])} messages")
if __name__ == "__main__":
    test_chat_conversation()