import webbrowser
from agent import ask_llm

def search_web(query):
    """Search the web and provide summary"""
    try:
        search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
        webbrowser.open(search_url)
        
        prompt = f"Search the web for: '{query}' and summarize the most relevant information in 3 sentences."
        summary = ask_llm(prompt)
        return f"🔍 Opened search for '{query}' in browser.\n\n🧠 Summary:\n{summary}"
    except Exception as e:
        return f"❌ Search failed: {str(e)}"