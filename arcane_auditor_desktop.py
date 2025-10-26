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
from arcane_paths import is_frozen

# When running as windowless app, uvicorn needs valid stdout/stderr
if is_frozen():
    import io
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

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
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        access_log=False  # Reduce console spam
    )


def main():
    """
    Main entry point for the desktop application.
    
    1. Start the web server in a background thread
    2. Wait for it to be ready
    3. Create and show the native window
    """
    
    # Load config to get host/port for window URL
    cfg = load_web_config(cli_args=None)
    host = cfg.get("host", DEFAULT_HOST)
    port = cfg.get("port", DEFAULT_PORT)
    
    # Create API instance for JavaScript bridge
    api = Api()
    
    # Start web server in a daemon thread
    # (daemon=True means it will shut down when main thread exits)
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give the server a moment to start up
    print("Starting Arcane Auditor Desktop...")
    time.sleep(2)  # Adjust if your server takes longer to start
    
    # Create the native window (make it global so API can access it)
    global window
    window = webview.create_window(
        title='Arcane Auditor',
        url=f'http://{host}:{port}',
        
        # Window size
        width=1400,
        height=900,
        
        # Window properties
        resizable=True,
        fullscreen=False,
        min_size=(1000, 700),  # Minimum window size
        
        # Appearance
        background_color='#1e293b',  # Matches your dark theme from style.css
        
        # Features
        text_select=True,  # Allow selecting text in the window
        
        # Window visibility
        hidden=False,
        on_top=False,
        
        # Confirmation dialog when closing
        confirm_close=False,  # Set to True if you want "Are you sure?" dialog
        
        # Expose API to JavaScript
        js_api=api
    )
    
    # Start the GUI event loop (this blocks until window is closed)
    # When user closes the window, the daemon thread will automatically stop
    webview.start(
        debug=False,  # Set to True during development for debug console
        http_server=False  # We're using our own server
    )
    
    print("Arcane Auditor Desktop closed.")


if __name__ == '__main__':
    main()