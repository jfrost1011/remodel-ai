import pandas as pd
import numpy as np
from typing import List, Dict
import random
import json
import os
class TrainingPairGenerator:
    def __init__(self):
        # Load the cleaned data
        csv_path = '../../../remodel-ai-data/processed/cleaned_data_all.csv'
        if not os.path.exists(csv_path):
            csv_path = '../../../remodel-ai-data/cleaned_remodeling_data_1000.csv'
        self.df = pd.read_csv(csv_path)
        print(f"Loaded {len(self.df)} rows from {csv_path}")
    def create_positive_pairs(self) -> List[Dict]:
        """Create similar project pairs (positive examples)"""
        positive_pairs = []
        # Group by project type and location for similar pairs
        for idx, row in self.df.iterrows():
            # Find similar projects (same type, same location)
            similar = self.df[
                (self.df['Remodel Type'] == row['Remodel Type']) &
                (self.df['Location'] == row['Location']) &
                (self.df.index != idx)
            ]
            if len(similar) > 0:
                for _, sim_row in similar.head(2).iterrows():
                    text1 = self._create_project_text(row)
                    text2 = self._create_project_text(sim_row)
                    positive_pairs.append({
                        'text1': text1,
                        'text2': text2,
                        'label': 1.0,
                        'similarity_reason': 'same type and location'
                    })
        return positive_pairs
    def create_negative_pairs(self) -> List[Dict]:
        """Create dissimilar project pairs (negative examples)"""
        negative_pairs = []
        for idx, row in self.df.iterrows():
            # Find dissimilar projects (different type OR location)
            different = self.df[
                ((self.df['Remodel Type'] != row['Remodel Type']) |
                 (self.df['Location'] != row['Location'])) &
                (self.df.index != idx)
            ]
            if len(different) > 0:
                for _, diff_row in different.sample(min(2, len(different))).iterrows():
                    text1 = self._create_project_text(row)
                    text2 = self._create_project_text(diff_row)
                    similarity_reason = []
                    if row['Remodel Type'] != diff_row['Remodel Type']:
                        similarity_reason.append('different type')
                    if row['Location'] != diff_row['Location']:
                        similarity_reason.append('different location')
                    negative_pairs.append({
                        'text1': text1,
                        'text2': text2,
                        'label': 0.0,
                        'similarity_reason': ' and '.join(similarity_reason)
                    })
        return negative_pairs
    def create_query_document_pairs(self) -> List[Dict]:
        """Create query-document pairs for better retrieval"""
        query_doc_pairs = []
        query_templates = [
            "How much does a {project_type} cost in {location}?",
            "What's the cost range for {project_type} in {location}?",
            "I need an estimate for {project_type} in {location}",
            "What's the timeline for {project_type} in {location}?",
            "How long does {project_type} take in {location}?"
        ]
        for idx, row in self.df.iterrows():
            # Create queries for this project
            project_type = row['Remodel Type'].replace('_', ' ')
            location = row['Location']
            # Create document text
            doc_text = self._create_project_text(row)
            # Create multiple queries for same document
            for template in query_templates[:2]:  # Use 2 queries per doc
                query = template.format(
                    project_type=project_type,
                    location=location
                )
                query_doc_pairs.append({
                    'text1': query,
                    'text2': doc_text,
                    'label': 1.0,
                    'similarity_reason': 'query-document match'
                })
                # Create negative example with wrong location
                wrong_location = random.choice(['Phoenix', 'Portland', 'Seattle', 'Las Vegas'])
                wrong_query = template.format(
                    project_type=project_type,
                    location=wrong_location
                )
                query_doc_pairs.append({
                    'text1': wrong_query,
                    'text2': doc_text,
                    'label': 0.0,
                    'similarity_reason': 'location mismatch'
                })
        return query_doc_pairs
    def _create_project_text(self, row) -> str:
        """Create descriptive text for a project"""
        return (f"{row['Remodel Type'].replace('_', ' ')} project in {row['Location']}. "
                f"Cost range: ${row['Average Cost (Low)']:,.0f} to ${row['Average Cost (High)']:,.0f}. "
                f"Timeline: {row['Average Time (weeks/other unit)']}.")
    def generate_balanced_dataset(self) -> pd.DataFrame:
        """Generate a balanced dataset for training"""
        print("Generating positive pairs...")
        positive_pairs = self.create_positive_pairs()
        print(f"Created {len(positive_pairs)} positive pairs")
        print("Generating negative pairs...")
        negative_pairs = self.create_negative_pairs()
        print(f"Created {len(negative_pairs)} negative pairs")
        print("Generating query-document pairs...")
        query_doc_pairs = self.create_query_document_pairs()
        print(f"Created {len(query_doc_pairs)} query-document pairs")
        # Balance the dataset
        min_count = min(len(positive_pairs), len(negative_pairs), len(query_doc_pairs))
        positive_pairs = random.sample(positive_pairs, min(min_count, len(positive_pairs)))
        negative_pairs = random.sample(negative_pairs, min(min_count, len(negative_pairs)))
        query_doc_pairs = random.sample(query_doc_pairs, min(min_count, len(query_doc_pairs)))
        # Combine all pairs
        all_pairs = positive_pairs + negative_pairs + query_doc_pairs
        random.shuffle(all_pairs)
        return pd.DataFrame(all_pairs)
if __name__ == "__main__":
    generator = TrainingPairGenerator()
    training_df = generator.generate_balanced_dataset()
    # Split into train/validation
    train_size = int(0.8 * len(training_df))
    train_df = training_df[:train_size]
    val_df = training_df[train_size:]
    # Save datasets
    train_df.to_csv('train_pairs.csv', index=False)
    val_df.to_csv('val_pairs.csv', index=False)
    # Save as JSON for Hugging Face
    train_df.to_json('train_pairs.json', orient='records', indent=2)
    val_df.to_json('val_pairs.json', orient='records', indent=2)
    print(f"\nGenerated {len(train_df)} training pairs and {len(val_df)} validation pairs")
    print(f"Positive examples: {len(training_df[training_df['label'] == 1.0])}")
    print(f"Negative examples: {len(training_df[training_df['label'] == 0.0])}")
    # Show sample pairs
    print("\nSample training pairs:")
    for i, row in train_df.head(3).iterrows():
        print(f"\nPair {i+1}:")
        print(f"Text1: {row['text1'][:100]}...")
        print(f"Text2: {row['text2'][:100]}...")
        print(f"Label: {row['label']}")
        print(f"Reason: {row['similarity_reason']}")
