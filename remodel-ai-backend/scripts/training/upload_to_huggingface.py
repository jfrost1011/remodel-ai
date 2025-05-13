from datasets import Dataset, DatasetDict
import pandas as pd
from huggingface_hub import login, create_repo
import os
import sys
# Get Hugging Face token
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
if not HUGGINGFACE_TOKEN:
    print("ERROR: Please set HUGGINGFACE_TOKEN environment variable")
    print("\nSteps to get your token:")
    print("1. Create account at https://huggingface.co/join")
    print("2. Go to https://huggingface.co/settings/tokens")
    print("3. Create new token with 'write' permission")
    print("4. Run in PowerShell: $env:HUGGINGFACE_TOKEN = 'hf_...'")
    sys.exit(1)
try:
    # Login to Hugging Face
    print("Logging in to Hugging Face...")
    login(token=HUGGINGFACE_TOKEN, add_to_git_credential=True)
    print("Login successful!")
except Exception as e:
    print(f"Login failed: {e}")
    sys.exit(1)
# Load the training data
print("\nLoading training data...")
train_df = pd.read_csv('train_pairs.csv')
val_df = pd.read_csv('val_pairs.csv')
print(f"Loaded {len(train_df)} training and {len(val_df)} validation pairs")
# Create dataset dict
dataset = DatasetDict({
    'train': Dataset.from_pandas(train_df),
    'validation': Dataset.from_pandas(val_df)
})
# Get your username
username = "jfrost10"  # UPDATE THIS!
dataset_name = f"{username}/remodelai-embeddings"
print(f"\nCreating repository: {dataset_name}")
try:
    create_repo(dataset_name, repo_type="dataset", exist_ok=True, private=False)
    print("Repository created successfully!")
except Exception as e:
    print(f"Repository creation warning: {e}")
print("\nUploading dataset...")
try:
    dataset.push_to_hub(dataset_name)
    print(f"Dataset successfully uploaded to: https://huggingface.co/datasets/{dataset_name}")
except Exception as e:
    print(f"Upload failed: {e}")
    sys.exit(1)
print("\nDataset upload complete!")
print("\nNext steps:")
print("1. Go to https://huggingface.co/autotrain")
print("2. Click 'New Project'")
print(f"3. Select dataset: {dataset_name}")
print("4. Choose 'Sentence Transformers' as the task")
print("5. Select 'sentence-transformers/all-MiniLM-L6-v2' as base model")
print("6. Configure training parameters (check dataset README)")
print("7. Start training!")
