import os
import sys
import pandas as pd
import numpy as np
from typing import List, Dict
from pinecone import Pinecone
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import logging
import time
# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Load environment variables
load_dotenv()
class DataLoader:
    def __init__(self):
        # Initialize Pinecone
        self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        self.index_name = os.getenv('PINECONE_INDEX')
        # Create index if it doesn't exist
        existing_indexes = self.pc.list_indexes().names()
        if self.index_name not in existing_indexes:
            logger.info(f"Creating index {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric='cosine'
            )
            # Wait for index to be ready
            time.sleep(10)
        self.index = self.pc.Index(self.index_name)
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
    def load_csv_data(self, csv_path: str):
        """Load data from CSV file"""
        logger.info(f"Loading data from {csv_path}")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} records")
        return df
    def prepare_documents(self, df: pd.DataFrame) -> List[Dict]:
        """Prepare documents for embedding"""
        documents = []
        for idx, row in df.iterrows():
            # Create comprehensive text for each project
            location = str(row.get('Location', 'Unknown'))
            remodel_type = str(row.get('Remodel Type', 'Unknown'))
            cost_low = float(row.get('Average Cost (Low)', 0))
            cost_high = float(row.get('Average Cost (High)', 0))
            timeline = str(row.get('Average Time (weeks/other unit)', 'Unknown'))
            source = str(row.get('Source URL', 'Unknown'))
            text = f"""
            Project Type: {remodel_type}
            Location: {location}
            Cost Range: ${cost_low:,.0f} - ${cost_high:,.0f}
            Average Cost: ${(cost_low + cost_high) / 2:,.0f}
            Timeline: {timeline}
            Source: {source}
            This is a {remodel_type} project in {location}. 
            The cost typically ranges from ${cost_low:,.0f} to ${cost_high:,.0f}.
            The average timeline for this project is {timeline}.
            """
            # Check if it's a California project
            is_ca = location.lower() in ['san diego', 'los angeles', 'la', 'sd']
            metadata = {
                'project_id': f'proj_{idx}',
                'remodel_type': remodel_type,
                'location': location,
                'cost_low': cost_low,
                'cost_high': cost_high,
                'cost_average': (cost_low + cost_high) / 2,
                'timeline': timeline,
                'source_url': source,
                'is_california': is_ca
            }
            documents.append({
                'id': f'doc_{idx}',
                'text': text.strip(),
                'metadata': metadata
            })
        logger.info(f"Prepared {len(documents)} documents")
        return documents
    def embed_and_store(self, documents: List[Dict], batch_size: int = 50):
        """Embed documents and store in Pinecone"""
        total_docs = len(documents)
        logger.info(f"Embedding and storing {total_docs} documents")
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i+batch_size]
            texts = [doc['text'] for doc in batch]
            try:
                # Generate embeddings
                embeddings = self.embeddings.embed_documents(texts)
                # Prepare vectors for Pinecone
                vectors = []
                for doc, embedding in zip(batch, embeddings):
                    vectors.append({
                        'id': doc['id'],
                        'values': embedding,
                        'metadata': doc['metadata']
                    })
                # Upsert to Pinecone
                self.index.upsert(vectors=vectors)
                logger.info(f"Processed batch {i//batch_size + 1}/{(total_docs//batch_size) + 1}")
                # Add small delay to avoid rate limits
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {str(e)}")
                continue
        logger.info("All documents embedded and stored successfully!")
    def verify_data(self):
        """Verify data was loaded correctly"""
        stats = self.index.describe_index_stats()
        logger.info(f"Index stats: {stats}")
        # Test query
        test_query = "kitchen remodel in San Diego"
        test_embedding = self.embeddings.embed_query(test_query)
        results = self.index.query(
            vector=test_embedding,
            top_k=3,
            include_metadata=True
        )
        logger.info("Test query results:")
        for match in results['matches']:
            logger.info(f"Score: {match['score']:.4f}")
            logger.info(f"Metadata: {match.get('metadata', {})}")
            logger.info("---")
if __name__ == "__main__":
    # Possible CSV paths
    csv_paths = [
        "../remodel-ai-data/processed/cleaned_data_all.csv",
        "../remodel-ai-data/cleaned_remodeling_data_1000.csv",
        "../../remodel-ai-data/processed/cleaned_data_all.csv",
        "../../remodel-ai-data/cleaned_remodeling_data_1000.csv",
        "C:/Users/remodel-ai/remodel-ai-data/cleaned_remodeling_data_1000.csv"
    ]
    csv_path = None
    for path in csv_paths:
        if os.path.exists(path):
            csv_path = path
            logger.info(f"Found CSV file: {path}")
            break
    if not csv_path:
        logger.error("No CSV file found! Please check the data directory")
        logger.error(f"Looked in: {csv_paths}")
        sys.exit(1)
    try:
        # Initialize loader
        loader = DataLoader()
        # Load and process data
        df = loader.load_csv_data(csv_path)
        documents = loader.prepare_documents(df)
        loader.embed_and_store(documents)
        # Verify data
        loader.verify_data()
    except Exception as e:
        logger.error(f"Error during data loading: {str(e)}")
        raise