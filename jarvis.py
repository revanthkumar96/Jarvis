import pyttsx3
import datetime
import speech_recognition as sr
import wikipedia
import pyautogui
import webbrowser as wb
import pywhatkit
import requests
import pyperclip
import os
import json
import threading
import subprocess
import re
from dotenv import load_dotenv
from newsapi import NewsApiClient
from agent import ask_llm
from cctv_controller import CCTVController
from tools import email_tool, search_tool, launcher_tool, summarize_tool

# Load environment variables
load_dotenv()

# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
screenshot_dir = os.path.join(script_dir, 'screenshots')
data_path = os.path.join(script_dir, 'data.txt')
contacts_path = os.path.join(script_dir, 'contacts.json')

# Create necessary directories
os.makedirs(screenshot_dir, exist_ok=True)

# Initialize TTS engine in background
engine = None
def init_tts():
    global engine
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 200)
        engine.setProperty('volume', 0.9)
        # Warm up the engine
        engine.say(" ")
        engine.runAndWait()
    except Exception as e:
        print(f"TTS init error: {e}")

threading.Thread(target=init_tts, daemon=True).start()

# Initialize CCTV controller
cctv = CCTVController()

def speak(text):
    """Convert text to speech efficiently"""
    print(f"Jarvis: {text}")
    if engine:
        try:
            def speak_thread():
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    print(f"Speech error: {e}")
            threading.Thread(target=speak_thread, daemon=True).start()
        except:
            pass

def load_contacts():
    """Load contacts from JSON file"""
    if os.path.exists(contacts_path):
        try:
            with open(contacts_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_contacts(contacts):
    """Save contacts to JSON file"""
    with open(contacts_path, 'w') as f:
        json.dump(contacts, f, indent=2)

contacts = load_contacts()

def time():
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"The current time is {current_time}")

def date():
    current_date = datetime.datetime.now().strftime("%B %d, %Y")
    speak(f"Today is {current_date}")

def greeting():
    hour = datetime.datetime.now().hour
    if 1 <= hour < 12:
        speak("Good Morning Sir!")
    elif 12 <= hour < 18:
        speak("Good Afternoon Sir!")
    else:
        speak("Good Evening Sir!")

def wishme():
    speak("Welcome Back Sir!")
    greeting()
    time()
    date()
    speak("Jarvis at your service. How can I assist you today?")

def takeCommandMIC():
    """Listen to microphone with improved recognition"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            r.adjust_for_ambient_noise(source, duration=0.5)
            r.pause_threshold = 0.8
            print("Listening...")
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
            
            print("Recognizing...")
            query = r.recognize_google(audio, language="en-US")
            print(f"User: {query}")
            return query.lower()
        except sr.WaitTimeoutError:
            return "none"
        except sr.UnknownValueError:
            speak("I didn't catch that. Could you repeat?")
            return "none"
        except Exception as e:
            print(f"Recognition error: {e}")
            return "none"

def sendEmail(to, subject, body):
    """Send email using email tool"""
    result = email_tool.send_email(subject, body, to)
    speak(result.replace("✅", "").replace("❌", "Error:"))

def get_news():
    """Get latest news"""
    if not os.getenv("NEWS_API_KEY"):
        speak("News API key missing.")
        return
    
    try:
        newsapi = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
        data = newsapi.get_top_headlines(category='technology', language='en', page_size=3)
        
        if not data['articles']:
            speak("No tech news available.")
            return
            
        headlines = [article['title'] for article in data['articles']]
        speak("Top tech news: " + ". ".join(headlines))
    except Exception as e:
        speak("News service unavailable.")
        print(f"News error: {e}")

def send_whatsapp(phone_no, message):
    """Send WhatsApp message with timeout"""
    try:
        def send_thread():
            try:
                pywhatkit.sendwhatmsg_instantly(phone_no, message, 15, tab_close=True)
                speak("Message sent.")
            except Exception as e:
                speak("Failed to send WhatsApp.")
                print(f"WhatsApp error: {e}")
        
        threading.Thread(target=send_thread).start()
        speak("Sending message now...")
    except:
        speak("WhatsApp service unavailable.")

def search_google(query=None):
    """Search Google using search tool"""
    if not query or query == "none":
        speak("What should I search for?")
        query = takeCommandMIC()
    
    if query != "none" and query.strip():
        try:
            result = search_tool.search_web(query)
            # Extract summary from result
            if "Summary:" in result:
                summary = result.split("Summary:")[1].strip()
                speak(f"Showing results for {query}. Summary: {summary}")
            else:
                wb.open(f'https://google.com/search?q={query.replace(" ", "+")}')
                speak(f"Showing results for {query}")
        except Exception as e:
            speak("Search failed.")
            print(f"Search error: {e}")

def read_clipboard():
    """Read clipboard content with summarization"""
    try:
        text = pyperclip.paste().strip()
        if not text:
            speak("Clipboard is empty.")
            return
            
        if len(text) > 500:
            speak("Content is long. Summarizing...")
            summary = summarize_tool.summarize_text(text)
            speak(summary)
        else:
            speak(f"Clipboard says: {text}")
    except Exception as e:
        speak("Clipboard access failed.")
        print(f"Clipboard error: {e}")

def take_screenshot():
    """Take screenshot efficiently"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(screenshot_dir, f'screenshot_{timestamp}.png')
        pyautogui.screenshot(filename)
        speak("Screenshot saved")
    except Exception as e:
        speak("Screenshot failed.")
        print(f"Screenshot error: {e}")

def get_weather(city=None):
    """Get weather with city detection"""
    if not os.getenv("WEATHER_API_KEY"):
        speak("Weather API key missing.")
        return
    
    if not city:
        speak("Which city?")
        city = takeCommandMIC()
        if city == "none":
            city = "Sydney"
    
    try:
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={os.getenv("WEATHER_API_KEY")}'
        res = requests.get(url, timeout=5)
        data = res.json()
        
        if res.status_code == 200:
            temp = round(data['main']['temp'])
            desc = data['weather'][0]['description']
            speak(f"In {city}, it's {temp}°C with {desc}")
        else:
            speak("Weather service unavailable.")
    except Exception as e:
        speak("Weather check failed.")
        print(f"Weather error: {e}")

def remember_data(data):
    """Store important information"""
    try:
        with open(data_path, 'a') as f:
            f.write(f"{datetime.datetime.now()}: {data}\n")
        speak("I've remembered that")
    except Exception as e:
        speak("Failed to save note.")
        print(f"Remember error: {e}")

def recall_data():
    """Recall stored information"""
    try:
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                content = f.read()
                if content:
                    speak("Your notes: " + content.replace('\n', ', '))
                else:
                    speak("No notes saved.")
        else:
            speak("No notes yet.")
    except Exception as e:
        speak("Failed to access notes.")
        print(f"Recall error: {e}")

def add_contact():
    """Add new contact"""
    speak("Contact name?")
    name = takeCommandMIC()
    if name == "none": return
    
    speak("Phone number?")
    number = takeCommandMIC()
    if number == "none": return
    
    contacts[name] = number
    save_contacts(contacts)
    speak(f"Added {name}")

def open_app(app_name):
    """Open applications with CCTV admin handling"""
    app_map = {
        'code': [
            'C:\\Program Files\\Microsoft VS Code\\Code.exe',
            'code'
        ],
        'chrome': [
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        ],
        'documents': [
            'explorer C:\\Users\\%USERNAME%\\Documents'
        ],
        'spotify': [
            'C:\\Users\\%USERNAME%\\AppData\\Roaming\\Spotify\\Spotify.exe'
        ],
        # CCTV application mapping
        'cctv': ["use_controller"],
        'vms': ["use_controller"],
        'surveillance': ["use_controller"]
    }
    
    if app_name in app_map:
        # Special handling for CCTV
        if app_name in ['cctv', 'vms', 'surveillance']:
            result = cctv.open_cctv_app()
            speak(result.replace("✅", "").replace("❌", "Error:"))
            return

        # Handle other applications normally
        for path in app_map[app_name]:
            try:
                if '%' in path:
                    path = os.path.expandvars(path)
                
                if path == 'code':
                    os.system('code')
                elif path.startswith('explorer '):
                    os.system(path)
                else:
                    os.startfile(path)
                
                speak(f"Opening {app_name}")
                return
            except Exception as e:
                print(f"Open error: {e}")
                continue
        speak(f"Failed to open {app_name}")
    else:
        speak("Application not configured")

def open_file_by_name():
    """Open file using launcher tool"""
    speak("What file should I open?")
    filename = takeCommandMIC()
    if filename != "none":
        result = launcher_tool.open_file_by_name(filename)
        speak(result.replace("✅", "").replace("❌", "Error:"))

def process_command(query):
    """Process commands with natural language understanding"""
    query = query.lower().strip()
    if not query or query == "none": return True
    
    print(f"Processing: {query}")
    
    # Time/Date
    if any(word in query for word in ['time', 'clock']):
        time()
    elif any(word in query for word in ['date', 'today', 'day']):
        date()
    
    # Information
    elif 'wikipedia' in query:
        topic = re.sub(r'search|wikipedia', '', query).strip()
        if topic:
            try:
                result = wikipedia.summary(topic, sentences=2)
                speak(f"According to Wikipedia: {result}")
            except:
                speak("Information not found")
        else:
            speak("What should I search?")
    
    elif 'search' in query and 'google' in query:
        search_google(re.sub(r'search google for', '', query).strip())
    
    elif 'youtube' in query:
        topic = re.sub(r'search youtube for|play', '', query).strip()
        if not topic:
            speak("What should I search?")
            topic = takeCommandMIC()
        if topic != "none":
            try:
                pywhatkit.playonyt(topic)
                speak(f"Playing {topic}")
            except:
                speak("YouTube access failed")
    
    # Communication
    elif 'email' in query:
        speak("Recipient's email?")
        to_email = takeCommandMIC()
        if to_email != "none":
            speak("Subject?")
            subject = takeCommandMIC()
            if subject != "none":
                speak("Message?")
                body = takeCommandMIC()
                if body != "none":
                    sendEmail(to_email, subject, body)
    
    elif 'whatsapp' in query or 'message' in query:
        if 'add contact' in query:
            add_contact()
        else:
            speak("Who to message?")
            contact = takeCommandMIC()
            if contact in contacts:
                speak("Your message?")
                message = takeCommandMIC()
                if message != "none":
                    send_whatsapp(contacts[contact], message)
            else:
                speak(f"Contact not found. Say 'add contact' to add {contact}")
    
    # System
    elif 'screenshot' in query:
        take_screenshot()
    elif 'read' in query and 'clipboard' in query:
        read_clipboard()
    elif 'weather' in query:
        city = re.sub(r'weather in|weather', '', query).strip()
        get_weather(city)
    elif 'news' in query:
        get_news()
    elif 'remember' in query:
        data = re.sub(r'remember', '', query).strip()
        if not data:
            speak("What should I remember?")
            data = takeCommandMIC()
        if data != "none":
            remember_data(data)
    elif 'recall' in query or 'do you know' in query:
        recall_data()
    
    # Applications
    elif 'open' in query:
        if 'file' in query:
            open_file_by_name()
        else:
            app = re.sub(r'open', '', query).strip()
            if app:
                open_app(app)
    
    # CCTV Commands
    elif 'cctv' in query or 'surveillance' in query or 'camera' in query:
        if 'status' in query:
            status = cctv.get_status()
            speak(f"Surveillance system is {status}")
        elif 'record' in query or 'start' in query:
            cctv.start_recording()
            speak("Recording started")
        elif 'stop' in query:
            cctv.stop_recording()
            speak("Recording stopped")
        elif 'view' in query or 'show' in query:
            camera_id = re.search(r'camera (\d+)', query)
            if camera_id:
                camera_id = camera_id.group(1)
                feed_url = cctv.get_camera_feed(camera_id)
                speak(f"Showing camera {camera_id}")
                wb.open(feed_url)
            else:
                open_app('cctv')
        else:
            open_app('cctv')
    
    # Control
    elif any(word in query for word in ['exit', 'quit', 'bye', 'goodbye']):
        speak("Goodbye Sir! Have a great day.")
        return False
    elif 'help' in query:
        speak("I can: tell time/date, search web/YouTube, send emails/messages, "
              "read news/weather, take screenshots, remember notes, open apps/files, "
              "and control CCTV systems. Say 'exit' when done.")
    
    # AI Fallback
    else:
        response = ask_llm(f"User said: {query}. Respond concisely as Jarvis assistant.")
        speak(response)
    
    return True

def main():
    """Main function with optimized loop"""
    print("Starting Jarvis Assistant...")
    wishme()
    
    while True:
        try:
            print("\nListening for commands...")
            query = takeCommandMIC()
            
            if 'jarvis' in query:
                clean_query = query.replace('jarvis', '').strip()
                if not process_command(clean_query):
                    break
            elif query != "none":
                speak("Please say 'Jarvis' before your command")
                
        except KeyboardInterrupt:
            speak("Goodbye!")
            break
        except Exception as e:
            print(f"Main error: {e}")
            speak("Sorry, let's try that again")

if __name__ == "__main__":
    main()