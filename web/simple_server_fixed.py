#!/usr/bin/env python3
"""
Simple HTTP server for the HTML frontend of Arcane Auditor.
This serves the simple HTML/JavaScript interface without requiring Node.js or React.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import webbrowser
import time

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ArcaneAuditorHandler(SimpleHTTPRequestHandler):
    """Custom handler for Arcane Auditor API endpoints."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/rules':
            self.handle_get_rules()
        elif parsed_path.path == '/api/configs':
            self.handle_get_configs()
        elif parsed_path.path.startswith('/api/config/'):
            config_name = parsed_path.path.split('/')[-1]
            self.handle_get_config(config_name)
        elif parsed_path.path == '/':
            self.serve_file('index.html')
        else:
            # Try to serve static files
            self.serve_static_file(parsed_path.path)
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/analyze':
            self.handle_analyze()
        elif parsed_path.path == '/api/download/excel':
            self.handle_download_excel()
        elif parsed_path.path == '/api/config':
            self.handle_save_config()
        else:
            self.send_error(404, "Not Found")
    
    def serve_file(self, filename):
        """Serve a file from the simple-frontend directory."""
        frontend_dir = Path(__file__).parent / 'simple-frontend'
        file_path = frontend_dir / filename
        
        if file_path.exists() and file_path.is_file():
            self.send_response(200)
            if filename.endswith('.html'):
                self.send_header('Content-type', 'text/html')
            elif filename.endswith('.css'):
                self.send_header('Content-type', 'text/css')
            elif filename.endswith('.js'):
                self.send_header('Content-type', 'application/javascript')
            else:
                self.send_header('Content-type', 'application/octet-stream')
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "File not found")
    
    def serve_static_file(self, path):
        """Serve static files, defaulting to index.html for unknown paths."""
        if path == '/':
            path = '/index.html'
        
        # Remove leading slash
        filename = path.lstrip('/')
        if not filename:
            filename = 'index.html'
        
        self.serve_file(filename)
    
    def handle_analyze(self):
        """Handle file analysis requests."""
        try:
            # Parse multipart form data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Get boundary from Content-Type header
            content_type = self.headers.get('Content-Type', '')
            if 'boundary=' not in content_type:
                self.send_error(400, "No boundary found in Content-Type")
                return
            
            boundary = content_type.split('boundary=')[1]
            
            # Extract file data
            file_data = None
            parts = post_data.split(f'--{boundary}'.encode())
            
            for part in parts:
                if b'Content-Disposition: form-data; name="file"' in part:
                    # Extract file content
                    file_start = part.find(b'\r\n\r\n') + 4
                    file_end = part.rfind(b'\r\n')
                    if file_end == -1:
                        file_end = len(part)
                    file_data = part[file_start:file_end]
                    break
            
            if not file_data:
                self.send_error(400, "No file uploaded")
                return
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                temp_file.write(file_data)
                temp_file_path = temp_file.name
            
            try:
                # Run analysis
                result = self.run_analysis(temp_file_path)
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            finally:
                # Clean up temp file
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.send_error(500, f"Analysis failed: {str(e)}")
    
    def run_analysis(self, zip_path):
        """Run the analysis on the uploaded ZIP file."""
        try:
            # Import your analysis modules only when needed
            from file_processing.processor import FileProcessor
            from parser.rules_engine import RulesEngine
            
            # Process the file
            processor = FileProcessor()
            pmd_model = processor.process_zip_file(zip_path)
            
            # Run rules
            rules_engine = RulesEngine()
            findings = rules_engine.analyze_pmd_model(pmd_model)
            
            # Format results
            zip_filename = Path(zip_path).name
            result = {
                'zip_filename': zip_filename,
                'total_files': len(pmd_model.files) if hasattr(pmd_model, 'files') else 0,
                'total_rules': len(rules_engine.get_enabled_rules()),
                'findings': [
                    {
                        'file_path': finding.file_path,
                        'line': finding.line,
                        'column': finding.column,
                        'rule_id': finding.rule_id,
                        'message': finding.message,
                        'severity': finding.severity
                    }
                    for finding in findings
                ]
            }
            
            return result
            
        except ImportError as e:
            # If modules aren't available, return a demo response
            zip_filename = Path(zip_path).name
            return {
                'zip_filename': zip_filename,
                'total_files': 1,
                'total_rules': 5,
                'findings': [
                    {
                        'file_path': 'demo.pmd',
                        'line': 10,
                        'column': 5,
                        'rule_id': 'DemoRule',
                        'message': 'This is a demo finding - install dependencies to run real analysis',
                        'severity': 'INFO'
                    }
                ]
            }
        except Exception as e:
            raise Exception(f"Analysis error: {str(e)}")
    
    def handle_download_excel(self):
        """Handle Excel download requests."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            findings = data.get('findings', [])
            
            # Create Excel file
            try:
                from output.formatter import ExcelFormatter
                formatter = ExcelFormatter()
                excel_data = formatter.format_findings(findings)
            except ImportError:
                # If ExcelFormatter isn't available, create a simple CSV
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['File Path', 'Line', 'Column', 'Rule ID', 'Message', 'Severity'])
                
                for finding in findings:
                    writer.writerow([
                        finding.get('file_path', ''),
                        finding.get('line', ''),
                        finding.get('column', ''),
                        finding.get('rule_id', ''),
                        finding.get('message', ''),
                        finding.get('severity', '')
                    ])
                
                excel_data = output.getvalue().encode()
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            self.send_header('Content-Disposition', 'attachment; filename="arcane-auditor-results.xlsx"')
            self.end_headers()
            self.wfile.write(excel_data)
            
        except Exception as e:
            self.send_error(500, f"Download failed: {str(e)}")
    
    def handle_get_rules(self):
        """Handle get rules request."""
        try:
            from parser.rules_engine import RulesEngine
            rules_engine = RulesEngine()
            rules = rules_engine.get_all_rules()
            
            rules_data = [
                {
                    'name': rule.__class__.__name__,
                    'description': getattr(rule, 'description', 'No description available'),
                    'enabled': rule.__class__.__name__ in rules_engine.get_enabled_rules(),
                    'severity': 'default'
                }
                for rule in rules
            ]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'rules': rules_data}).encode())
            
        except ImportError:
            # If modules aren't available, return demo rules
            demo_rules = [
                {
                    'name': 'DemoRule1',
                    'description': 'Demo rule for testing - install dependencies for real rules',
                    'enabled': True,
                    'severity': 'default'
                },
                {
                    'name': 'DemoRule2', 
                    'description': 'Another demo rule',
                    'enabled': False,
                    'severity': 'default'
                }
            ]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'rules': demo_rules}).encode())
            
        except Exception as e:
            self.send_error(500, f"Failed to get rules: {str(e)}")
    
    def handle_get_configs(self):
        """Handle get configurations request."""
        try:
            configs_dir = project_root / 'configs'
            configs = []
            
            if configs_dir.exists():
                for config_file in configs_dir.glob('*.json'):
                    try:
                        with open(config_file, 'r') as f:
                            config_data = json.load(f)
                            rules_count = len(config_data.get('rules', {}))
                            configs.append({
                                'name': config_file.stem,
                                'rules_count': rules_count
                            })
                    except Exception:
                        continue
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'configurations': configs}).encode())
            
        except Exception as e:
            self.send_error(500, f"Failed to get configs: {str(e)}")
    
    def handle_get_config(self, config_name):
        """Handle get specific configuration request."""
        try:
            config_path = project_root / 'configs' / f'{config_name}.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(config_data).encode())
            else:
                self.send_error(404, "Configuration not found")
                
        except Exception as e:
            self.send_error(500, f"Failed to get config: {str(e)}")
    
    def handle_save_config(self):
        """Handle save configuration request."""
        try:
            # Parse multipart form data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Simple parsing - extract name and config_data
            name = None
            config_data = None
            
            parts = post_data.split(b'\r\n')
            for i, part in enumerate(parts):
                if b'name=' in part:
                    name = part.split(b'name=')[1].decode().strip()
                elif b'config_data=' in part:
                    config_data = part.split(b'config_data=')[1].decode().strip()
            
            if not name or not config_data:
                self.send_error(400, "Missing name or config data")
                return
            
            # Save configuration
            config_path = project_root / 'configs' / f'{name}.json'
            with open(config_path, 'w') as f:
                json.dump(json.loads(config_data), f, indent=2)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
            
        except Exception as e:
            self.send_error(500, f"Failed to save config: {str(e)}")


def start_server(port=8080):
    """Start the simple HTTP server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ArcaneAuditorHandler)
    
    print(f"🚀 Simple Arcane Auditor server starting on http://localhost:{port}")
    print(f"📁 Serving files from: {Path(__file__).parent / 'simple-frontend'}")
    print(f"🔮 No Node.js or React required!")
    print(f"🌐 Open your browser to: http://localhost:{port}")
    print(f"⏹️  Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped")
        httpd.shutdown()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Arcane Auditor HTTP Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to run server on (default: 8080)')
    parser.add_argument('--open-browser', action='store_true', help='Automatically open browser')
    
    args = parser.parse_args()
    
    if args.open_browser:
        # Open browser after a short delay
        def open_browser():
            time.sleep(1)
            webbrowser.open(f'http://localhost:{args.port}')
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
    
    start_server(args.port)
