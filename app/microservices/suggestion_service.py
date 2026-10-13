# app/microservices/suggestion_service.py

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def get_smart_suggestions(past_tasks, input_text: str, top_n: int = 3):
    if not past_tasks or not input_text.strip():
        return []

    task_texts = list(set(t["task"] for t in past_tasks if t.get("task")))
    if not task_texts:
        return []

    task_embeddings = model.encode(task_texts)
    input_embedding = model.encode([input_text])

    similarities = cosine_similarity(input_embedding, task_embeddings)[0]
    top_indices = np.argsort(similarities)[-top_n:][::-1]
    return [task_texts[i] for i in top_indices]
