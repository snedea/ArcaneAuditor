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
from arcane_paths import is_frozen, resource_path
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
    
    1. Show splash screen with logo
    2. Start the web server in a background thread
    3. Wait for it to be ready
    4. Show the main window and close splash
    """
    
    # Load config to get host/port for window URL
    cfg = load_web_config(cli_args=None)
    host = cfg.get("host", DEFAULT_HOST)
    port = cfg.get("port", DEFAULT_PORT)
    
    # Create API instance for JavaScript bridge
    api = Api()
    
    # Get logo as base64 data URI
    logo_data = get_logo_base64()
    
    # Create logo HTML - use image if available, fallback to simple placeholder
    if logo_data:
        debug_log("DEBUG: Using logo image (embedded)")
        logo_html = f'<img src="{logo_data}" alt="Arcane Auditor" class="logo-img">'
    else:
        debug_log("DEBUG: Using simple text placeholder")
        # Use a simple div with background gradient instead of complex SVG
        logo_html = '<div class="logo-placeholder" style="width: 200px; height: 200px; margin: 0 auto; background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 80px;">🧙</div>'
    
    # Load splash screen HTML template
    try:
        splash_path = Path(resource_path("web/frontend/splash.html"))
        debug_log(f"DEBUG: Loading splash from: {splash_path}")
        
        if splash_path.exists():
            with open(splash_path, 'r', encoding='utf-8') as f:
                splash_html = f.read()
            # Replace placeholder with actual logo HTML
            splash_html = splash_html.replace('<!-- LOGO_PLACEHOLDER -->', logo_html)
            debug_log("DEBUG: Splash HTML loaded from file")
        else:
            debug_log("WARNING: splash.html not found, using inline fallback")
            raise FileNotFoundError("splash.html not found")
    except Exception as e:
        debug_log(f"WARNING: Could not load splash.html: {e}")
        # Fallback to inline HTML if file not found
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
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    overflow: hidden;
                }}
                .logo-container {{ text-align: center; animation: fadeIn 0.5s ease-out; }}
                .logo-img {{ width: 250px; height: 250px; margin-bottom: 30px; animation: pulse 2s ease-in-out infinite; }}
                .logo-placeholder {{ width: 200px; height: 200px; margin: 0 auto 30px; animation: pulse 2s ease-in-out infinite; }}
                h1 {{ font-size: 42px; font-weight: 700; color: #60a5fa; margin-bottom: 15px; letter-spacing: 3px; }}
                p {{ font-size: 16px; color: #94a3b8; margin-bottom: 30px; }}
                .spinner {{ width: 40px; height: 40px; margin: 0 auto; border: 4px solid #334155;
                    border-top-color: #60a5fa; border-radius: 50%; animation: spin 1s linear infinite; }}
                @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
                @keyframes pulse {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.05); }} }}
                @keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
            </style>
        </head>
        <body>
            <div class="logo-container">
                {logo_html}
                <h1>ARCANE AUDITOR</h1>
                <p>Initializing the Weave...</p>
                <div class="spinner"></div>
            </div>
        </body>
        </html>
        '''
    
    # Create splash screen window
    debug_log("Starting Arcane Auditor Desktop...")
    
    # Get screen size using tkinter (cross-platform)
    try:
        import tkinter as tk
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
    except:
        # Fallback if tkinter not available
        screen_width = 1920
        screen_height = 1080
    
    # Calculate center position for splash window
    # Make it larger for better visibility on modern displays
    window_width = 600
    window_height = 600
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
        background_color='#ffffff'
    )
    
    # Start web server in a daemon thread
    # (daemon=True means it will shut down when main thread exits)
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Function to create main window after server is ready
    def create_main_window():
        import urllib.request
        import urllib.error
        
        # Minimum 3 seconds to show the splash screen
        time.sleep(3)
        
        # Poll the API to see when server is ready (max 10 seconds)
        max_attempts = 20
        for attempt in range(max_attempts):
            try:
                urllib.request.urlopen(f'http://{host}:{port}/api/configs', timeout=1)
                print(f"Server is ready after {attempt + 1} attempts")
                break
            except urllib.error.URLError:
                time.sleep(0.5)
                if attempt == max_attempts - 1:
                    print("Warning: Server did not start in time, continuing anyway")
        
        # Create the native window (make it global so API can access it)
        global window
        window = webview.create_window(
            title='Arcane Auditor',
            url=f'http://{host}:{port}',
            
            # Window size - fullscreen=False for windowed fullscreen
            width=1400,
            height=900,
            
            # Window properties
            resizable=True,
            fullscreen=False,  # Changed to False for windowed fullscreen
            min_size=(1000, 700),
            
            # Appearance
            background_color='#1e293b',
            
            # Features
            text_select=True,
            
            # Window visibility - start hidden, will show after splash
            hidden=True,
            on_top=False,
            
            # Confirmation dialog when closing
            confirm_close=False,
            
            # Expose API to JavaScript
            js_api=api
        )
        
        # Wait a moment for window to be ready
        time.sleep(0.5)
        
        # Show main window and close splash with fade effect
        window.show()
        splash.destroy()
    
    # Start main window creation in a thread
    window_thread = threading.Thread(target=create_main_window, daemon=True)
    window_thread.start()
    
    # Start the GUI event loop for splash screen
    # This will transition to main window when splash is destroyed
    webview.start(
        debug=False,
        http_server=False
    )
    
    print("Arcane Auditor Desktop closed.")


if __name__ == '__main__':
    main()