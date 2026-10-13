# chatbot/ai_homework_generator.py
from openai import OpenAI
import os

# Set your OpenAI API key (preferably via .env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def generate_homework(subject: str, class_level: str, score: float = None) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
    Generate a simple homework task for a student studying in class {class_level} for the subject {subject}.
    Keep it short and actionable. {'Consider the student is weak in this subject based on their recent low score.' if score and score < 60 else ''}
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{ "role": "user", "content": prompt }],
        max_tokens=100
    )
    return response.choices[0].message.content.strip()
