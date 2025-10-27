"""
Arcane Auditor Desktop Application

Runs the FastAPI web server in a background thread and displays the UI
in a native desktop window using pywebview.

No browser, no console - just a clean desktop application.
"""

import webview
import threading
import time
import sys
import os
from pathlib import Path
from arcane_paths import is_frozen, resource_path, user_root

def debug_log(message):
    """Debug logging - disabled for production"""
    pass

debug_log("="*60)
debug_log("Arcane Auditor Desktop Starting")
debug_log("="*60)

# DON'T redirect stdout/stderr here - we need to see errors during startup
# Redirect AFTER webview is created if needed for uvicorn

# Add the project root to Python path (same as server.py does)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the FastAPI app and uvicorn
try:
    from web.server import app, load_web_config, ensure_sample_rule_config
    import uvicorn
except ImportError as e:
    print(f"Error: Could not import web server components: {e}")
    print("Make sure web/server.py exists and all dependencies are installed.")
    sys.exit(1)

# Default host and port for the web server
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080


def get_logo_base64():
    """Load pre-optimized splash logo and return as base64 data URI or None if not found"""
    try:
        import base64
        
        splash_logo_path = Path(resource_path("assets/arcane-auditor-splash.webp"))
        
        if splash_logo_path.exists():
            debug_log(f"DEBUG: Loading splash logo from: {splash_logo_path}")
            with open(splash_logo_path, 'rb') as f:
                img_data = f.read()
                base64_data = base64.b64encode(img_data).decode('utf-8')
            debug_log(f"DEBUG: Splash logo loaded, {len(base64_data)} chars base64")
            return f"data:image/webp;base64,{base64_data}"
        else:
            debug_log("DEBUG: Splash logo not found")
    except Exception as e:
        debug_log(f"WARNING: Could not load logo: {e}")
        import traceback
        traceback.print_exc()
    
    # Fallback to simple text if logo not found
    debug_log("DEBUG: Using simple text fallback")
    return None


class Api:
    """API class to expose Python functions to JavaScript in the desktop app"""
    
    def download_file(self, job_id):
        """Handle file downloads - auto-save to Downloads folder"""
        import requests
        from datetime import datetime
        
        # Load config to get the correct host/port
        cfg = load_web_config(cli_args=None)
        host = cfg.get("host", DEFAULT_HOST)
        port = cfg.get("port", DEFAULT_PORT)
        
        try:
            # Download from the API using actual config
            response = requests.get(f'http://{host}:{port}/api/download/{job_id}')
            
            if response.status_code == 200:
                # Auto-save to Downloads folder
                downloads_folder = Path.home() / "Downloads"
                downloads_folder.mkdir(parents=True, exist_ok=True)
                
                # Include timestamp to avoid overwriting
                timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
                filename = f"arcane-auditor-results-{timestamp}.xlsx"
                save_path = downloads_folder / filename
                
                # Save the file
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                return {'success': True, 'path': str(save_path), 'filename': filename}
            else:
                return {'success': False, 'error': f'Server returned status {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}


def run_server():
    """
    Start the FastAPI/Uvicorn server in the background.
    Uses the same configuration as the regular web server but skips browser opening.
    """
    # Load config (without CLI args, so uses defaults/config file)
    cfg = load_web_config(cli_args=None)
    
    host = cfg.get("host", DEFAULT_HOST)
    port = cfg.get("port", DEFAULT_PORT)
    log_level = cfg.get("log_level", "info")
    
    # Ensure sample rule config is seeded (from server.py)
    ensure_sample_rule_config()
    
    print(f"Starting Arcane Auditor server on http://{host}:{port}")
    
    # Start uvicorn server (without opening browser since we have pywebview)
    # Use critical log level in frozen mode to avoid console output issues
    uvicorn_log_level = "critical" if is_frozen() else log_level
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=uvicorn_log_level,
        access_log=False  # Reduce console spam
    )


def main():
    """
    Main entry point for the desktop application.
    
    Shows splash with logo IMMEDIATELY, then initializes everything in background.
    """
    
    # Load logo FIRST (fast - 83KB webp loads instantly)
    logo_html = '<div class="logo-placeholder">🧙</div>'  # Fallback
    try:
        import base64
        splash_logo_path = Path(resource_path("assets/arcane-auditor-splash.webp"))
        with open(splash_logo_path, 'rb') as f:
            img_data = f.read()
            base64_data = base64.b64encode(img_data).decode('utf-8')
        logo_html = f'<img src="data:image/webp;base64,{base64_data}" alt="Arcane Auditor" class="logo-img">'
    except Exception as e:
        # If logo missing, app is probably broken anyway, but fail gracefully
        print(f"Warning: Could not load splash logo: {e}")
        logo_html = '<div class="logo-placeholder">🧙</div>'
    
    # Inline splash with logo embedded
    splash_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                width: 100%; height: 100vh; display: flex; flex-direction: column;
                justify-content: center; align-items: center; background: #0f172a;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}
            .logo-img {{ 
                width: 250px; height: 250px; margin-bottom: 30px; 
                animation: pulse 2s ease-in-out infinite; 
            }}
            .logo-placeholder {{ 
                width: 200px; height: 200px; margin: 0 auto 30px; 
                background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%); 
                border-radius: 50%; display: flex; align-items: center; 
                justify-content: center; font-size: 80px;
                animation: pulse 2s ease-in-out infinite;
            }}
            h1 {{ font-size: 42px; font-weight: 700; color: #60a5fa; 
                 margin-bottom: 15px; letter-spacing: 3px; }}
            p {{ font-size: 16px; color: #94a3b8; margin-bottom: 30px; }}
            .spinner {{ 
                width: 40px; height: 40px; margin: 0 auto; 
                border: 4px solid #334155; border-top-color: #60a5fa; 
                border-radius: 50%; animation: spin 1s linear infinite; 
            }}
            @keyframes pulse {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.05); }} }}
            @keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
        </style>
    </head>
    <body>
        {logo_html}
        <h1>ARCANE AUDITOR</h1>
        <p>Initializing the Weave...</p>
        <div class="spinner"></div>
    </body>
    </html>
    '''
    
    # Get screen dimensions quickly
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
    except:
        screen_width = 1920
        screen_height = 1080
    
    window_width = 600
    window_height = 600
    x_pos = (screen_width - window_width) // 2
    y_pos = (screen_height - window_height) // 2
    
    # CREATE SPLASH IMMEDIATELY with logo embedded
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
    
    # NOW do all the heavy initialization in background
    def initialize_and_start():
        # Load config
        cfg = load_web_config(cli_args=None)
        host = cfg.get("host", DEFAULT_HOST)
        port = cfg.get("port", DEFAULT_PORT)
        
        # Create API instance
        api = Api()
        
        # Start server
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to be ready
        time.sleep(3)  # Minimum splash time
        
        import urllib.request
        import urllib.error
        
        max_attempts = 20
        for attempt in range(max_attempts):
            try:
                urllib.request.urlopen(f'http://{host}:{port}/api/configs', timeout=1)
                break
            except urllib.error.URLError:
                time.sleep(0.5)
        
        # Prepare storage
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
            js_api=api,
            private_mode=False,
            storage_path=storage_dir,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        time.sleep(0.5)
        window.show()
        splash.destroy()
    
    # Start initialization in background thread
    init_thread = threading.Thread(target=initialize_and_start, daemon=True)
    init_thread.start()
    
    # Start GUI event loop - splash shows while initialization happens
    webview.start(debug=False, http_server=False)
    
    print("Arcane Auditor Desktop closed.")
if __name__ == '__main__':
    main()