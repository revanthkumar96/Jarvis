import requests
import os
import time
import subprocess
import ctypes
import pyautogui
import threading
from dotenv import load_dotenv

load_dotenv()

class CCTVController:
    def __init__(self, base_url=None, username=None, password=None):
        self.base_url = base_url or os.getenv("CCTV_URL")
        self.username = username or os.getenv("CCTV_USER")
        self.password = password or os.getenv("CCTV_PASS")
        self.session = requests.Session()
        self.authenticated = False
        self.cctv_path = os.getenv("CCTV_PATH", "C:\\Program Files\\VMS\\VMS.exe")
        
    def is_admin(self):
        """Check if running as administrator"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def run_as_admin(self, cmd):
        """Run command as administrator"""
        try:
            if self.is_admin():
                # Already admin, run directly
                subprocess.Popen(cmd, shell=True)
                return True
            else:
                # Request admin privileges
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", cmd, None, None, 1
                )
                return True
        except Exception as e:
            print(f"Admin execution error: {e}")
            return False
    
    def auto_login_gui(self):
        """Automatically handle GUI login after 3 seconds"""
        def login_thread():
            try:
                time.sleep(3)  # Wait for app to load
                
                # Try to find and fill login fields
                username = self.username or os.getenv("CCTV_USER", "admin")
                password = self.password or os.getenv("CCTV_PASS", "password")
                
                # Method 1: Try typing directly (if fields are focused)
                pyautogui.typewrite(username)
                pyautogui.press('tab')
                pyautogui.typewrite(password)
                pyautogui.press('enter')
                
                print("Auto-login attempted")
                
            except Exception as e:
                print(f"Auto-login error: {e}")
        
        # Start auto-login in background
        threading.Thread(target=login_thread, daemon=True).start()
    
    def open_cctv_app(self):
        """Open CCTV application with admin privileges and auto-login"""
        try:
            if not os.path.exists(self.cctv_path):
                return f"❌ CCTV application not found at: {self.cctv_path}"
            
            # Method 1: Try running with admin privileges
            if self.run_as_admin(f'"{self.cctv_path}"'):
                print("✅ CCTV app launched with admin privileges")
                
                # Start auto-login process
                if self.username and self.password:
                    self.auto_login_gui()
                
                return "✅ CCTV application opened successfully"
            else:
                return "❌ Failed to launch CCTV with admin privileges"
                
        except Exception as e:
            return f"❌ CCTV launch error: {str(e)}"
    
    def authenticate(self):
        """Authenticate with CCTV system via API"""
        if not self.authenticated:
            try:
                auth_url = f"{self.base_url}/login"
                response = self.session.post(auth_url, json={
                    "username": self.username,
                    "password": self.password
                }, timeout=3)
                
                if response.status_code == 200:
                    self.authenticated = True
                    return True
            except:
                pass
        return self.authenticated
    
    def get_status(self):
        """Get system status"""
        try:
            if self.authenticate():
                status_url = f"{self.base_url}/status"
                response = self.session.get(status_url, timeout=3)
                return response.json().get('status', 'unknown')
        except:
            pass
        return "offline"
    
    def start_recording(self):
        """Start recording"""
        try:
            if self.authenticate():
                record_url = f"{self.base_url}/record/start"
                self.session.post(record_url)
        except:
            pass
    
    def stop_recording(self):
        """Stop recording"""
        try:
            if self.authenticate():
                record_url = f"{self.base_url}/record/stop"
                self.session.post(record_url)
        except:
            pass
    
    def get_camera_feed(self, camera_id):
        """Get camera feed URL"""
        return f"{self.base_url}/camera/{camera_id}/feed"