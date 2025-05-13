from sentence_transformers import SentenceTransformer, InputExample, losses
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
from torch.utils.data import DataLoader
import pandas as pd
import torch
from datetime import datetime
import os
# Load data
print("Loading training data...")
train_df = pd.read_csv('train_pairs.csv')
val_df = pd.read_csv('val_pairs.csv')
# Create training examples
print("Creating training examples...")
train_examples = []
for idx, row in train_df.iterrows():
    train_examples.append(InputExample(
        texts=[row['text1'], row['text2']], 
        label=float(row['label'])
    ))
# Create validation examples
val_examples = []
for idx, row in val_df.iterrows():
    val_examples.append(InputExample(
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
# Create evaluator
sentences1 = [ex.texts[0] for ex in val_examples[:100]]
sentences2 = [ex.texts[1] for ex in val_examples[:100]]
scores = [ex.label for ex in val_examples[:100]]
evaluator = EmbeddingSimilarityEvaluator(sentences1, sentences2, scores)
# Train model
print("Starting training...")
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    evaluator=evaluator,
    epochs=3,
    evaluation_steps=500,
    warmup_steps=int(len(train_dataloader) * 0.1),
    output_path='remodelai-finetuned-local',
    save_best_model=True,
    show_progress_bar=True
)
print("Training complete! Model saved to 'remodelai-finetuned-local'")
# Push to Hugging Face
try:
    print("Pushing to Hugging Face...")
    model.save_to_hub(
        "jfrost10/remodelai-embeddings-finetuned",
        token=os.getenv('HUGGINGFACE_TOKEN'),
        exist_ok=True,
        replace_model_card=True
    )
    print("Model pushed to Hugging Face!")
except Exception as e:
    print(f"Error pushing to hub: {e}")
    print("Model saved locally at 'remodelai-finetuned-local'")
