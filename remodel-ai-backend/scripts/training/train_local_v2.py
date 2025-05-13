from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
import pandas as pd
import os
from datetime import datetime
print("Loading training data...")
train_df = pd.read_csv('train_pairs.csv')
val_df = pd.read_csv('val_pairs.csv')
print(f"Loaded {len(train_df)} training and {len(val_df)} validation samples")
# Create training examples
print("Creating training examples...")
train_examples = []
for idx, row in train_df.iterrows():
    train_examples.append(InputExample(
        texts=[row['text1'], row['text2']], 
        label=float(row['label'])
    ))
# Load model
print("Loading base model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
# Create DataLoader
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
# Define loss function
train_loss = losses.CosineSimilarityLoss(model)
# Train model - simplified version
print("Starting training...")
epochs = 3
warmup_steps = int(len(train_dataloader) * 0.1)
output_path = 'remodelai-finetuned-local'
# Train without evaluator to simplify
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=epochs,
    warmup_steps=warmup_steps,
    output_path=output_path,
    show_progress_bar=True
)
print(f"Training complete! Model saved to '{output_path}'")
# Push to Hugging Face with authentication
print("Pushing to Hugging Face...")
try:
    from huggingface_hub import login
    login(token=os.getenv('HUGGINGFACE_TOKEN'))
    model_name = "jfrost10/remodelai-embeddings-finetuned"
    model.save_to_hub(
        model_name,
        exist_ok=True
    )
    print(f"Model successfully pushed to: https://huggingface.co/{model_name}")
    print(f"You can use this model with: SentenceTransformer('{model_name}')")
except Exception as e:
    print(f"Error pushing to hub: {e}")
    print("Model saved locally at 'remodelai-finetuned-local'")
