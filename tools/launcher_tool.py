import os
import webbrowser

def open_file_by_name(filename, search_path=None):
    """Open file by name"""
    if not search_path:
        user_home = os.path.expanduser("~")
        search_dirs = [
            os.path.join(user_home, "Desktop"),
            os.path.join(user_home, "Documents"),
            os.path.join(user_home, "Downloads"),
        ]
    else:
        search_dirs = [search_path]
    
    matched_files = []
    for directory in search_dirs:
        for root, _, files in os.walk(directory):
            if filename in files:
                matched_files.append(os.path.join(root, filename))
    
    if not matched_files:
        return f"❌ File '{filename}' not found"
    
    try:
        file_path = os.path.abspath(matched_files[0])
        webbrowser.open(f"file://{file_path}")
        return f"✅ Opened: {file_path}"
    except Exception as e:
        return f"❌ Failed to open file: {str(e)}"