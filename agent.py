import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def ask_llm(prompt: str, model="llama3-8b-8192") -> str:
    """Get response from LLM"""
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=256
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM error: {e}")
        return "I'm having trouble processing that request."