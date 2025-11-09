"""
Arcane Auditor Desktop Application

Runs the FastAPI web server in a background thread and displays the UI
in a native desktop window using pywebview.

No browser, no console - just a clean desktop application.
"""

# MINIMAL imports first - only what we need for splash
import webview
from webview.menu import Menu, MenuAction
import threading
import time
import sys
import os
import json
from pathlib import Path


window = None
desktop_api = None


def _wait_for_js_ready(window, timeout=5.0, interval=0.25):
    attempts = int(timeout / interval)
    for _ in range(attempts):
        try:
            ready = window.evaluate_js("Boolean(window.DialogManagerReady)")
            if isinstance(ready, str):
                ready = ready.lower() == 'true'
            if ready:
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


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
    
    def check_for_updates(self):
        """Manual check for updates triggered from menu."""
        try:
            from utils.update_checker import check_for_updates
            result = check_for_updates(force=True)
            return {
                'success': True,
                'update_available': result.get('update_available', False),
                'latest_version': result.get('latest_version', ''),
                'current_version': result.get('current_version', ''),
                'error': result.get('error')
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'update_available': False}
    
    def get_update_preferences(self):
        """Get current update preferences."""
        try:
            from utils.preferences_manager import get_update_prefs
            updates = get_update_prefs()
            return {
                'success': True,
                'enabled': updates.get('enabled', False),
                'first_run_completed': updates.get('first_run_completed', False)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def set_update_preferences(self, enabled):
        """Toggle update detection and persist to preferences."""
        try:
            from utils.preferences_manager import get_update_prefs, set_update_prefs
            updates = get_update_prefs()
            updates['enabled'] = bool(enabled)
            if set_update_prefs(updates):
                return {'success': True}
            else:
                return {'success': False, 'error': 'Failed to save preferences'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


def show_immediate_splash():
    """Create and show a minimal splash screen with logo"""
    
    # Load logo
    logo_html = '<div style="width: 500px; height: 500px; margin: 0 auto; background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 100px;">🧙</div>'
    
    try:
        from utils.arcane_paths import resource_path
        import base64
        
        splash_logo_path = Path(resource_path("assets/arcane-auditor-splash.webp"))
        if splash_logo_path.exists():
            with open(splash_logo_path, 'rb') as f:
                img_data = f.read()
                base64_data = base64.b64encode(img_data).decode('utf-8')
            logo_html = f'<img src="data:image/webp;base64,{base64_data}" style="width: 500px; height: 500px; object-fit: contain;">'
    except Exception as e:
        print(f"Could not load logo: {e}")
    
    # Simple splash HTML
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
                overflow: hidden;
            }}
        </style>
    </head>
    <body>
        {logo_html}
    </body>
    </html>
    '''
    
    window_width = 500
    window_height = 500
    
    # Windows: Calculate center position
    # macOS: Omit x,y to let OS handle it (already works)
    if sys.platform == 'win32':
        import ctypes
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        x_pos = (screen_width - window_width) // 2
        y_pos = (screen_height - window_height) // 2
    else:
        x_pos = None
        y_pos = None
    
    # Import version for window title
    from __version__ import __version__
    
    splash = webview.create_window(
        title=f'Arcane Auditor v{__version__}',
        html=splash_html,
        width=window_width,
        height=window_height,
        x=x_pos,
        y=y_pos,
        frameless=True,
        on_top=True,
        background_color='#0f172a',
    )
    
    return splash

def main():
    """
    Main entry point for the desktop application.
    
    Check for read-only location, shows splash immediately, then loads everything else in background.
    """ 
    
    # ========================================================================
    # CRITICAL: Check for read-only location BEFORE showing splash
    # This handles DMGs with no write access due to mounting as read-only.
    # ========================================================================
    from utils.dmg_detector import check_and_exit_if_dmg
    
    # Check for DMG and exit if found
    check_and_exit_if_dmg()
    
    # Show splash IMMEDIATELY before heavy imports
    splash = show_immediate_splash()

    # NOW do heavy imports and initialization in background
    def initialize_app():
        # Heavy imports happen here (after splash is visible)
        from utils.arcane_paths import is_frozen
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
        global desktop_api
        api = Api(host, port)
        desktop_api = api
        
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
        
        
        # Create main window first (needed for menu callbacks)
        global window
        from __version__ import __version__
        
        # Helper functions for menu callbacks
        def check_updates_callback():
            """Menu callback for checking updates."""
            try:
                result = api.check_for_updates()
                if result.get('success'):
                    if result.get('update_available'):
                        latest = result.get('latest_version', '')
                        current = result.get('current_version', '')
                        _show_alert(
                            window,
                            f"Update available!\n\n"
                            f"Current version: {current}\n"
                            f"Latest version: {latest}\n\n"
                            f"Visit GitHub Releases to download."
                        )
                    else:
                        _show_alert(window, "You are running the latest version!")
                else:
                    error = result.get('error', 'Unknown error')
                    _show_alert(window, f"Update check failed: {error}")
            except Exception as e:
                _show_alert(window, f"Error checking for updates: {e}")
        
        def toggle_update_detection_callback():
            """Menu callback for toggling update detection."""
            _toggle_update_detection(window, api)
        
        # Create menu bar using pywebview Menu API
        menu = [
            Menu('File', [
                Menu('About', [
                    MenuAction('Check for Updates', check_updates_callback)
                ])
            ]),
            Menu('Options', [
                MenuAction('Enable Update Detection', toggle_update_detection_callback)
            ])
        ]
        
        window = webview.create_window(
            title=f'Arcane Auditor v{__version__}',
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
            menu=menu
        )
        
        # Wait for window to be ready
        time.sleep(0.5)
        
        # Show main window and close splash
        window.show()
        splash.destroy()

    
    # Start initialization in background thread
    init_thread = threading.Thread(target=initialize_app, daemon=True)
    init_thread.start()

    # Prepare storage directory
    from utils.arcane_paths import user_root
    storage_dir = os.path.join(user_root(), '.user_preferences')
    os.makedirs(storage_dir, exist_ok=True)
    
    def on_app_ready():
        def try_handle_first_run():
            try:
                if window is not None and desktop_api is not None:
                    _handle_first_run_and_updates(window, desktop_api)
                else:
                    threading.Timer(0.5, try_handle_first_run).start()
            except Exception as e:
                print(f"Error running first-run/update handler: {e}")

        try_handle_first_run()

    # Start GUI event loop - splash shows while initialization happens
    webview.start(
        debug=False,
        http_server=False,
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        private_mode=False,
        storage_path=storage_dir,
        func=on_app_ready
    )
    
    print("Arcane Auditor Desktop closed.")


def _show_alert(window, message):
    """Show an alert dialog using JavaScript."""
    js_message = json.dumps(str(message))
    try:
        if _wait_for_js_ready(window):
            script = (
                "(() => {"
                "const manager = window.DialogManager;"
                f"if (!manager || typeof manager.showAlert !== 'function') {{ return window.alert({js_message}); }}"
                f"return manager.showAlert({js_message});"
                "})()"
            )
            window.evaluate_js(script)
            return
    except Exception as e:
        print(f"Error showing alert via DialogManager: {e}")

    try:
        window.evaluate_js(f"alert({js_message});")
    except Exception as e:
        print(f"Error showing alert: {e}")
        print(f"Message: {message}")


def _show_confirmation(window, title, message):
    """Show a confirmation dialog using the shared frontend helper."""

    def native_confirmation():
        try:
            return bool(window.create_confirmation_dialog(title, message))
        except Exception as native_error:
            print(f"Native confirmation dialog unavailable: {native_error}. Falling back to basic JS confirm.")
            script = f"confirm({json.dumps(f'{title}\\n\\n{message} (OK = Enable, Cancel = Disable)')});"
            try:
                result = window.evaluate_js(script)
                if isinstance(result, str):
                    return result.lower() == 'true'
                return bool(result)
            except Exception as fallback_error:
                print(f"Error showing fallback JS confirm: {fallback_error}")
                return False

    if not _wait_for_js_ready(window):
        print("DialogManager not ready, falling back to native confirmation dialog.")
        return native_confirmation()

    lines = [line.strip() for line in message.split('\n') if line.strip()]
    payload = json.dumps({
        "title": title,
        "lines": lines,
    })

    made_on_top = False
    try:
        if hasattr(window, "set_on_top"):
            try:
                window.set_on_top(True)
                made_on_top = True
            except Exception:
                pass

        init_script = (
            "(() => {"
            "const manager = window.DialogManager;"
            "if (!manager || typeof manager.showUpdatePrompt !== 'function') { return 'missing'; }"
            "window.__aaUpdatePromptState = { ready: false };"
            f"manager.showUpdatePrompt({payload}).then(value => {{ window.__aaUpdatePromptState = {{ ready: true, value: Boolean(value) }}; }}).catch(error => {{ window.__aaUpdatePromptState = {{ ready: true, value: false, error: String(error) }}; }});"
            "return 'started';"
            "})()"
        )
        status = window.evaluate_js(init_script)
        if isinstance(status, str):
            status = status.strip('"')
        if status != 'started':
            raise RuntimeError('DialogManager unavailable')

        for _ in range(200):  # polling up to ~20 seconds
            state_json = window.evaluate_js("JSON.stringify(window.__aaUpdatePromptState)")
            if state_json and state_json != 'null':
                try:
                    state = json.loads(state_json)
                except json.JSONDecodeError:
                    state = None
                if isinstance(state, dict) and state.get('ready'):
                    value = bool(state.get('value', False))
                    window.evaluate_js(
                        "(() => {"
                        "if (window.DialogManager && typeof window.DialogManager.closeAll === 'function') { window.DialogManager.closeAll(); }"
                        "window.__aaUpdatePromptState = null;"
                        "})()"
                    )
                    return value
            time.sleep(0.1)

        # Timed out - close dialog and fall back
        window.evaluate_js(
            "(() => {"
            "if (window.DialogManager && typeof window.DialogManager.closeAll === 'function') { window.DialogManager.closeAll(); }"
            "window.__aaUpdatePromptState = null;"
            "})()"
        )
        print("Timed out waiting for DialogManager response; falling back to native dialog.")
        return native_confirmation()

    except Exception as helper_error:
        print(f"Custom update dialog unavailable: {helper_error}")
        return native_confirmation()
    finally:
        if made_on_top and hasattr(window, "set_on_top"):
            try:
                window.set_on_top(False)
            except Exception:
                pass


def _toggle_update_detection(window, api):
    """Toggle update detection preference."""
    try:
        from utils.preferences_manager import get_update_prefs, set_update_prefs
        updates = get_update_prefs()
        current_state = updates.get('enabled', False)
        new_state = not current_state
        
        updates['enabled'] = new_state
        if set_update_prefs(updates):
            status = "enabled" if new_state else "disabled"
            _show_alert(window, f"Update detection {status}")
        else:
            _show_alert(window, "Failed to save preference")
    except Exception as e:
        print(f"Error toggling update detection: {e}")


def _handle_first_run_and_updates(window, api):
    """Handle first-run dialog and background update check."""
    try:
        from utils.preferences_manager import get_update_prefs, set_update_prefs
        from utils.update_checker import check_for_updates
        
        updates = get_update_prefs()
        first_run_completed = updates.get('first_run_completed', False)
        update_enabled = updates.get('enabled', False)
        
        # Show first-run dialog if needed
        if not first_run_completed:
            message = (
                "Would you like Arcane Auditor to occasionally check for new versions?\n\n"
                "This is a read-only check that calls the GitHub API."
            )
            result = _show_confirmation(
                window,
                "Enable Update Detection?",
                message
            )
            
            updates['enabled'] = result
            updates['first_run_completed'] = True
            set_update_prefs(updates)
            update_enabled = result
        
        # Background update check if enabled
        if update_enabled:
            def background_update_check():
                """Background thread function for update checking."""
                try:
                    result = check_for_updates(force=False)
                    if result.get('update_available'):
                        latest = result.get('latest_version', '')
                        current = result.get('current_version', '')
                        _show_alert(
                            window,
                            f"Update available!\n\n"
                            f"Current version: {current}\n"
                            f"Latest version: {latest}\n\n"
                            f"Visit GitHub Releases to download."
                        )
                except Exception as e:
                    # Silent failure - don't bother user with errors
                    print(f"Background update check failed: {e}")
            
            # Spawn background thread (non-blocking)
            threading.Thread(target=background_update_check, daemon=True).start()
    except Exception as e:
        # Silent failure - don't block app startup
        print(f"Error in first-run/update handling: {e}")


if __name__ == '__main__':
    main()