import requests
import json
BASE_URL = "http://localhost:8000"
def test_chat():
    """Test chat endpoint with real queries"""
    queries = [
        "How much does a kitchen remodel cost in San Diego?",
        "What's the timeline for a bathroom remodel in Los Angeles?",
        "How much does a kitchen remodel cost in Phoenix?",  # Should reject - not in CA
        "Tell me about the weather",  # Should reject - not construction related
    ]
    for query in queries:
        print(f"\nQuery: {query}")
        payload = {
            "content": query,
            "role": "user"
        }
        response = requests.post(f"{BASE_URL}/api/v1/chat", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data['message'][:200]}...")
            print(f"Session ID: {data['session_id']}")
        else:
            print(f"Error: {response.status_code}")
def test_estimate():
    """Test estimate endpoint"""
    payload = {
        "project_details": {
            "project_type": "kitchen_remodel",
            "property_type": "single_family",
            "city": "San Diego",
            "state": "CA",
            "square_footage": 200,
            "additional_details": "Modern kitchen with island"
        }
    }
    print("\n\nTesting Estimate Endpoint...")
    response = requests.post(f"{BASE_URL}/api/v1/estimate", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"Estimate ID: {data['estimate_id']}")
        print(f"Total Cost: ${data['total_cost']:,.0f}")
        print(f"Cost Range: ${data['cost_range_low']:,.0f} - ${data['cost_range_high']:,.0f}")
        print(f"Timeline: {data['timeline']['total_days']} days")
        return data['estimate_id']
    else:
        print(f"Error: {response.status_code}")
        return None
def test_export(estimate_id):
    """Test export endpoint"""
    if not estimate_id:
        return
    payload = {
        "estimate_id": estimate_id,
        "format": "pdf"
    }
    print("\n\nTesting Export Endpoint...")
    response = requests.post(f"{BASE_URL}/api/v1/export", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"Export URL: {data['file_url']}")
        print(f"Download Name: {data['download_name']}")
    else:
        print(f"Error: {response.status_code}")
if __name__ == "__main__":
    print("Comprehensive RemodelAI API Test")
    print("=" * 50)
    test_chat()
    estimate_id = test_estimate()
    test_export(estimate_id)