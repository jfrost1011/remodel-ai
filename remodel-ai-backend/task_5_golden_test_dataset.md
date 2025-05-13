# Task 5: Creating a Golden Test Data Set
*?? **Task 5: Generate a synthetic test data set to baseline an initial evaluation with RAGAS***
To establish baseline performance metrics for our RemodelAI system, we generated a comprehensive test dataset of 44 queries (34 valid location, 10 invalid location) and evaluated 30 queries using RAGAS-inspired metrics:
| Metric | Value |
|--------|-------|
| Context Recall | 0.5000 |
| Faithfulness | 0.9000 |
| Factual Correctness | 0.8000 |
| Answer Relevancy | 0.4000 |
| Context Entity Recall | 0.0516 |
| Noise Sensitivity (Relevant) | 0.0923 |
The evaluation reveals excellent faithfulness (90%) - our system accurately distinguishes between valid (SD/LA) and invalid location queries, providing appropriate responses. Factual correctness at 80% indicates reliable cost estimation when numbers are provided.
However, context entity recall at 5.16% and answer relevancy at 40% highlight significant optimization opportunities. The system struggles to extract specific cost figures and timeline details from the knowledge base, often providing general information rather than direct answers to user queries.
Context recall at 50% suggests our retrieval mechanism captures relevant documents but fails to extract key numerical entities. The relatively low noise sensitivity (9.23%) is encouraging, showing consistent performance across similar queries.
Priority improvements based on these metrics:
1. **Enhance entity extraction**: Improve context entity recall from 5.16% through better chunking strategies that preserve numerical data
2. **Boost answer relevancy**: Increase from 40% by fine-tuning response generation to directly address cost and timeline questions
3. **Optimize retrieval**: Improve context recall from 50% with better embedding models that understand construction terminology
These baseline metrics establish clear targets for our fine-tuning efforts in Task 4.
