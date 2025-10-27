"""
Arcane Auditor Desktop Application

Runs the FastAPI web server in a background thread and displays the UI
in a native desktop window using pywebview.

No browser, no console - just a clean desktop application.
"""

# MINIMAL imports first - only what we need for splash
import webview
import threading
import time
import sys
import os
from pathlib import Path


class Api:
    """API class to expose Python functions to JavaScript in the desktop app"""
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
    
    def download_file(self, job_id):
        """Handle file downloads - auto-save to Downloads folder"""
        import requests
        from datetime import datetime
        
        try:
            response = requests.get(f'http://{self.host}:{self.port}/api/download/{job_id}')
            
            if response.status_code == 200:
                downloads_folder = Path.home() / "Downloads"
                downloads_folder.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
                filename = f"arcane-auditor-results-{timestamp}.xlsx"
                save_path = downloads_folder / filename
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                return {'success': True, 'path': str(save_path), 'filename': filename}
            else:
                return {'success': False, 'error': f'Server returned status {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}


def show_immediate_splash():
    """Create and show a minimal splash screen with logo"""
    
    # Default fallback logo
    logo_html = '<div style="width: 250px; height: 250px; margin: 0 auto; background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 100px;">🧙</div>'
    
    # Try to load actual logo
    try:
        from arcane_paths import resource_path
        import base64
        
        splash_logo_path = Path(resource_path("assets/arcane-auditor-splash.webp"))
        if splash_logo_path.exists():
            with open(splash_logo_path, 'rb') as f:
                img_data = f.read()
                base64_data = base64.b64encode(img_data).decode('utf-8')
            logo_html = f'<img src="data:image/webp;base64,{base64_data}" style="width: 250px; height: 250px;">'
    except Exception as e:
        print(f"Could not load logo: {e}")
    
    # Simple splash - just the logo centered on dark background
    splash_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                width: 100%; height: 100vh; display: flex;
                justify-content: center; align-items: center; 
                background: #0f172a;
            }}
        </style>
    </head>
    <body>
        {logo_html}
    </body>
    </html>
    '''
    
    # Get screen size quickly
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.update_idletasks()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
    except:
        screen_width = 1920
        screen_height = 1080
    
    window_width = 400
    window_height = 400
    x_pos = (screen_width - window_width) // 2
    y_pos = (screen_height - window_height) // 2
    
    splash = webview.create_window(
        title='Arcane Auditor',
        html=splash_html,
        width=window_width,
        height=window_height,
        x=x_pos,
        y=y_pos,
        frameless=True,
        on_top=True,
        background_color='#0f172a'
    )
    
    return splash


def main():
    """
    Main entry point for the desktop application.
    
    Shows splash immediately, then loads everything else in background.
    """
    
    # Show splash IMMEDIATELY before heavy imports
    splash = show_immediate_splash()
    
    # NOW do heavy imports and initialization in background
    def initialize_app():
        # Heavy imports happen here (after splash is visible)
        from arcane_paths import is_frozen, resource_path, user_root
        from web.server import app, load_web_config, ensure_sample_rule_config
        import uvicorn
        
        DEFAULT_HOST = "127.0.0.1"
        DEFAULT_PORT = 8080
        
        # Load config
        cfg = load_web_config(cli_args=None)
        host = cfg.get("host", DEFAULT_HOST)
        port = cfg.get("port", DEFAULT_PORT)
        log_level = cfg.get("log_level", "info")
        
        # Create API instance
        api = Api(host, port)
        
        # Start server
        def run_server():
            ensure_sample_rule_config()
            print(f"Starting Arcane Auditor server on http://{host}:{port}")
            uvicorn_log_level = "critical" if is_frozen() else log_level
            uvicorn.run(app, host=host, port=port, log_level=uvicorn_log_level, access_log=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to be ready
        time.sleep(3)  # Minimum display time for splash
        
        import urllib.request
        import urllib.error
        
        max_attempts = 20
        for attempt in range(max_attempts):
            try:
                urllib.request.urlopen(f'http://{host}:{port}/api/configs', timeout=1)
                print(f"Server ready after {attempt + 1} attempts")
                break
            except urllib.error.URLError:
                time.sleep(0.5)
                if attempt == max_attempts - 1:
                    print("Warning: Server did not start in time, continuing anyway")
        
        # Prepare storage directory
        storage_dir = os.path.join(user_root(), 'webview_storage')
        os.makedirs(storage_dir, exist_ok=True)
        
        # Create main window
        global window
        window = webview.create_window(
            title='Arcane Auditor',
            url=f'http://{host}:{port}',
            width=1400,
            height=900,
            resizable=True,
            fullscreen=False,
            min_size=(1000, 700),
            background_color='#1e293b',
            text_select=True,
            hidden=True,
            on_top=False,
            confirm_close=False,
            js_api=api
        )
        
        # Wait for window to be ready
        time.sleep(0.5)
        
        # Show main window and close splash
        window.show()
        splash.destroy()
    
    # Start initialization in background thread
    init_thread = threading.Thread(target=initialize_app, daemon=True)
    init_thread.start()
    
    # Prepare storage directory for webview
    storage_dir = os.path.join(os.path.expanduser("~"), ".pywebview")
    os.makedirs(storage_dir, exist_ok=True)
    
    # Start GUI event loop - splash shows while initialization happens
    webview.start(
        debug=False,
        http_server=False,
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        private_mode=False,
        storage_path=storage_dir
    )
    
    print("Arcane Auditor Desktop closed.")


if __name__ == '__main__':
    main()