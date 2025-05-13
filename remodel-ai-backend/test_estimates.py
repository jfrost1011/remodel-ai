import requests
import json
BASE_URL = "http://localhost:8000"
def test_various_estimates():
    """Test different types of estimate requests"""
    print("Testing Various Estimate Scenarios")
    print("=" * 50)
    test_cases = [
        {
            "name": "Small Kitchen in San Diego",
            "data": {
                "project_type": "kitchen_remodel",
                "property_type": "condo",
                "city": "San Diego",
                "state": "CA",
                "square_footage": 150
            }
        },
        {
            "name": "Large Bathroom in Los Angeles",
            "data": {
                "project_type": "bathroom_remodel",
                "property_type": "single_family",
                "city": "Los Angeles",
                "state": "CA",
                "square_footage": 200
            }
        },
        {
            "name": "ADU in LA",
            "data": {
                "project_type": "accessory_dwelling_unit",
                "property_type": "single_family",
                "city": "LA",
                "state": "CA",
                "square_footage": 600
            }
        }
    ]
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        response = requests.post(f"{BASE_URL}/api/v1/estimate/", json={
            "project_details": test_case['data']
        })
        if response.status_code == 200:
            data = response.json()
            print(f"  Total Cost: ${data['total_cost']:,}")
            print(f"  Range: ${data['cost_range_low']:,} - ${data['cost_range_high']:,}")
            print(f"  Timeline: {data['timeline']['total_days']} days")
        else:
            print(f"  Error: {response.status_code} - {response.text}")
if __name__ == "__main__":
    test_various_estimates()