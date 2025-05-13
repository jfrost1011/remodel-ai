import matplotlib.pyplot as plt
import json
# Load metrics
with open('baseline_ragas_metrics.json', 'r') as f:
    data = json.load(f)
metrics = data['metrics']
# Create bar chart
fig, ax = plt.subplots(figsize=(10, 6))
metrics_names = list(metrics.keys())
metrics_values = list(metrics.values())
# Color bars based on performance
colors = []
for value in metrics_values:
    if value >= 0.8:
        colors.append('green')
    elif value >= 0.6:
        colors.append('yellow')
    else:
        colors.append('red')
bars = ax.bar(metrics_names, metrics_values, color=colors)
# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.4f}',
            ha='center', va='bottom')
ax.set_ylim(0, 1.0)
ax.set_ylabel('Score')
ax.set_title('RemodelAI Baseline RAGAS Metrics')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('baseline_metrics_chart.png', dpi=300, bbox_inches='tight')
plt.show()
