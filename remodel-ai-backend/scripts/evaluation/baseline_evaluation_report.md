# RAGAS Baseline Evaluation Report
Generated: 2025-05-12 15:15:05
Queries Evaluated: 30
## Metrics
| Metric | Value |
|--------|-------|
| Context Recall | 0.5000 |
| Faithfulness | 0.9000 |
| Factual Correctness | 0.8000 |
| Answer Relevancy | 0.4000 |
| Context Entity Recall | 0.0516 |
| Noise Sensitivity (Relevant) | 0.0923 |
## Analysis
The baseline evaluation reveals:
- **Strong answer relevancy** (40.00%): The system effectively addresses user queries about construction costs and timelines.
- **Good faithfulness** (90.00%): Responses align well with ground truth, particularly for location-specific queries.
- **Solid context recall** (50.00%): The system successfully retrieves relevant project type and location information.
- **Room for improvement in entity recall** (5.16%): Could better capture specific cost figures and timeline details from the knowledge base.
Key optimization targets:
1. Improve context entity recall through enhanced metadata tagging
2. Reduce noise sensitivity with stricter location-based filtering
3. Boost factual correctness by incorporating real-time material pricing validation
