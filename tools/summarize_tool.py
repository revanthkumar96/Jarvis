from agent import ask_llm

def summarize_text(text: str):
    """Summarize text using LLM"""
    try:
        if len(text) > 10000:
            return "❌ Text too long for summarization"
            
        prompt = f"Summarize the following text in 3-4 bullet points:\n\n{text}"
        return ask_llm(prompt)
    except Exception as e:
        return f"❌ Summarization failed: {str(e)}"