import pandas as pd
import numpy as np
from typing import List, Dict
import json
import sys
import os
# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
class TestQueryGenerator:
    def __init__(self):
        # Load the cleaned data - adjust path as needed
        csv_path = '../../../remodel-ai-data/processed/cleaned_data_all.csv'
        # If that doesn't exist, try the original
        if not os.path.exists(csv_path):
            csv_path = '../../../remodel-ai-data/cleaned_remodeling_data_1000.csv'
        self.df = pd.read_csv(csv_path)
        print(f"Loaded {len(self.df)} rows from {csv_path}")
    def generate_test_queries(self, num_queries: int = 50) -> List[Dict]:
        """Generate synthetic test queries for RAGAS evaluation"""
        test_queries = []
        # Query templates for RemodelAI
        templates = [
            "How much does a {project_type} cost in {location}?",
            "What's the timeline for a {project_type} in {location}?",
            "I need a cost estimate for {project_type} in {location}",
            "What's the average price for {project_type} in {location}?",
            "Can you estimate the cost of {project_type} in {location}?",
            "I want to do a {project_type} in {location}, what will it cost?",
            "What's the price range for {project_type} in {location}?",
            "How long will a {project_type} take in {location}?",
            "What are the costs for {project_type} in {location} area?",
            "Can you give me an estimate for {project_type} project in {location}?"
        ]
        # Generate valid queries (80% - for SD/LA)
        valid_locations = ['San Diego', 'Los Angeles']
        project_types = self.df['Remodel Type'].unique()
        # Clean up project types
        project_types = [pt for pt in project_types if pd.notna(pt)]
        for i in range(int(num_queries * 0.8)):
            template = np.random.choice(templates)
            location = np.random.choice(valid_locations)
            project_type = np.random.choice(project_types)
            # Format project type for display
            display_type = project_type.replace('_', ' ')
            query = template.format(
                project_type=display_type,
                location=location
            )
            # Get ground truth from data
            relevant_data = self.df[
                (self.df['Location'] == location) &
                (self.df['Remodel Type'] == project_type)
            ]
            if len(relevant_data) > 0:
                avg_low = relevant_data['Average Cost (Low)'].mean()
                avg_high = relevant_data['Average Cost (High)'].mean()
                # Handle timeline data properly
                timeline_data = relevant_data['Average Time (weeks/other unit)'].dropna()
                if len(timeline_data) > 0:
                    # Get the most common timeline
                    avg_time = timeline_data.mode().iloc[0] if len(timeline_data.mode()) > 0 else timeline_data.iloc[0]
                else:
                    avg_time = "8-12 weeks"
                ground_truth = f"For {display_type} in {location}, costs typically range from ${avg_low:,.0f} to ${avg_high:,.0f}. Timeline is usually {avg_time}."
                test_queries.append({
                    'query': query,
                    'ground_truth': ground_truth,
                    'location': location,
                    'project_type': project_type,
                    'query_type': 'valid_location'
                })
        # Generate invalid location queries (20%)
        invalid_locations = ['Phoenix', 'San Francisco', 'Sacramento', 'Las Vegas', 'Portland', 'Seattle']
        for i in range(int(num_queries * 0.2)):
            template = np.random.choice(templates[:5])  # Use cost-focused templates
            location = np.random.choice(invalid_locations)
            project_type = np.random.choice(project_types)
            display_type = project_type.replace('_', ' ')
            query = template.format(
                project_type=display_type,
                location=location
            )
            ground_truth = f"We currently only serve San Diego and Los Angeles. We're not available in {location} yet, but we're expanding soon!"
            test_queries.append({
                'query': query,
                'ground_truth': ground_truth,
                'location': location,
                'project_type': project_type,
                'query_type': 'invalid_location'
            })
        return test_queries
if __name__ == "__main__":
    generator = TestQueryGenerator()
    test_queries = generator.generate_test_queries(50)
    # Save test queries
    with open('test_queries.json', 'w') as f:
        json.dump(test_queries, f, indent=2)
    # Also save as CSV for easy viewing
    pd.DataFrame(test_queries).to_csv('test_queries.csv', index=False)
    print(f"\nGenerated {len(test_queries)} test queries")
    print(f"Valid location queries: {sum(1 for q in test_queries if q['query_type'] == 'valid_location')}")
    print(f"Invalid location queries: {sum(1 for q in test_queries if q['query_type'] == 'invalid_location')}")
    # Show sample queries
    print("\nSample queries:")
    for i, q in enumerate(test_queries[:3]):
        print(f"\n{i+1}. {q['query']}")
        print(f"   Ground Truth: {q['ground_truth'][:100]}...")
