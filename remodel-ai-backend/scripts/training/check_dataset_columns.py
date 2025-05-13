from datasets import load_dataset
# Load the dataset from Hugging Face
dataset = load_dataset("jfrost10/remodelai-embeddings")
# Check the columns
print("Dataset columns:")
print(dataset['train'].column_names)
print("\nSample from train set:")
print(dataset['train'][0])
