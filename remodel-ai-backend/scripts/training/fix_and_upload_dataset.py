import pandas as pd
from datasets import Dataset, DatasetDict
from huggingface_hub import login
import os
# Login to Hugging Face
token = os.getenv('HUGGINGFACE_TOKEN')
login(token=token)
# Load the original data
train_df = pd.read_csv('train_pairs.csv')
val_df = pd.read_csv('val_pairs.csv')
# Create datasets with explicit types
train_dataset = Dataset.from_pandas(train_df, preserve_index=False)
val_dataset = Dataset.from_pandas(val_df, preserve_index=False)
# Create dataset dict
dataset_dict = DatasetDict({
    'train': train_dataset,
    'validation': val_dataset
})
# Push to hub with explicit format
dataset_dict.push_to_hub(
    "jfrost10/remodelai-embeddings-v2",
    private=False
)
print("Dataset uploaded successfully!")
print(f"View at: https://huggingface.co/datasets/jfrost10/remodelai-embeddings-v2")
