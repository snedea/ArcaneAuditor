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
from urllib.parse import urlparse
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
            # Try direct import first (if dependencies are available)
            from file_processing.processor import FileProcessor
            from parser.rules_engine import RulesEngine
            from parser.app_parser import ModelParser
            
            # Process the file
            processor = FileProcessor()
            source_files_map = processor.process_zip_file(zip_path)
            
            # Parse files into context
            pmd_parser = ModelParser()
            context = pmd_parser.parse_files(source_files_map)
            
            # Run rules
            rules_engine = RulesEngine()
            findings = rules_engine.run(context)
            
            # Format results
            zip_filename = Path(zip_path).name
            result = {
                'zip_filename': zip_filename,
                'total_files': len(source_files_map),
                'total_rules': len(rules_engine.rules),
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
            
        except ImportError:
            # If direct import fails, try uv run as fallback
            try:
                import subprocess
                import json as json_module
                
                # Use proper path escaping for Windows
                project_root_str = str(project_root).replace('\\', '\\\\')
                zip_path_str = str(zip_path).replace('\\', '\\\\')
                zip_filename_str = Path(zip_path).name.replace('\\', '\\\\')
                
                result = subprocess.run([
                    'uv', 'run', 'python', '-c', f'''
import sys
sys.path.insert(0, r"{project_root_str}")
from file_processing.processor import FileProcessor
from parser.rules_engine import RulesEngine
from parser.app_parser import ModelParser
import json

# Redirect stdout to stderr for debug messages, then restore for JSON output
original_stdout = sys.stdout
sys.stdout = sys.stderr

# Process the file
processor = FileProcessor()
source_files_map = processor.process_zip_file(r"{zip_path_str}")

# Parse files into context
pmd_parser = ModelParser()
context = pmd_parser.parse_files(source_files_map)

# Run rules
rules_engine = RulesEngine()
findings = rules_engine.run(context)

# Restore stdout for JSON output
sys.stdout = original_stdout

# Format results
result = {{
    "zip_filename": r"{zip_filename_str}",
    "total_files": len(source_files_map),
    "total_rules": len(rules_engine.rules),
    "findings": [
        {{
            "file_path": finding.file_path,
            "line": finding.line,
            "column": finding.column,
            "rule_id": finding.rule_id,
            "message": finding.message,
            "severity": finding.severity
        }}
        for finding in findings
    ]
}}

print(json.dumps(result))
'''
                ], capture_output=True, text=True, cwd=project_root)
                
                if result.returncode == 0:
                    stdout_content = result.stdout.strip()
                    if not stdout_content:
                        raise Exception("uv run produced no output")
                    try:
                        return json_module.loads(stdout_content)
                    except json_module.JSONDecodeError as e:
                        raise Exception(f"uv run produced invalid JSON: {e}. Output: {stdout_content[:200]}")
                else:
                    raise Exception(f"uv run failed (code {result.returncode}): {result.stderr}")
                    
            except (FileNotFoundError, subprocess.SubprocessError) as e:
                # uv not available or failed
                raise Exception(f"Analysis failed: uv run not available or failed: {str(e)}")
            
        except Exception as e:
            # Any other error during analysis
            raise Exception(f"Analysis failed: {str(e)}")
    
    def handle_download_excel(self):
        """Handle Excel download requests."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            findings = data.get('findings', [])
            
            # Create Excel file
            try:
                # Try to import openpyxl - if not available, fall back to CSV
                import openpyxl
                from openpyxl.styles import Font, PatternFill, Alignment
                from openpyxl.utils import get_column_letter
                from pathlib import Path
                
                # Create workbook
                wb = openpyxl.Workbook()
                
                # Remove default sheet
                wb.remove(wb.active)
                
                # Group findings by file
                findings_by_file = {}
                for finding in findings:
                    file_path = finding.get('file_path', 'Unknown')
                    if file_path not in findings_by_file:
                        findings_by_file[file_path] = []
                    findings_by_file[file_path].append(finding)
                
                # Create summary sheet
                summary_sheet = wb.create_sheet("Summary")
                summary_sheet.append(["Analysis Summary"])
                summary_sheet.append(["Total Issues", len(findings)])
                
                # Count by severity
                severe_count = len([f for f in findings if f.get('severity') == 'SEVERE'])
                warning_count = len([f for f in findings if f.get('severity') == 'WARNING'])
                info_count = len([f for f in findings if f.get('severity') == 'INFO'])
                
                summary_sheet.append(["Severe", severe_count])
                summary_sheet.append(["Warnings", warning_count])
                summary_sheet.append(["Info", info_count])
                summary_sheet.append([])
                summary_sheet.append(["File", "Issues", "Severe", "Warnings", "Info"])
                
                # Style summary sheet
                summary_sheet['A1'].font = Font(bold=True, size=14)
                for row in range(1, 8):
                    summary_sheet[f'A{row}'].font = Font(bold=True)
                
                # Create sheets for each file
                for file_path, file_findings in findings_by_file.items():
                    # Clean sheet name (Excel has restrictions)
                    sheet_name = Path(file_path).stem[:31]  # Excel sheet name limit
                    sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    if not sheet_name:
                        sheet_name = "Unknown"
                    
                    ws = wb.create_sheet(sheet_name)
                    
                    # Headers
                    headers = ["Rule ID", "Severity", "Line", "Column", "Message", "File Path"]
                    ws.append(headers)
                    
                    # Style headers
                    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                    header_font = Font(color="FFFFFF", bold=True)
                    for col_num, header in enumerate(headers, 1):
                        cell = ws.cell(row=1, column=col_num)
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = Alignment(horizontal="center")
                    
                    # Add findings
                    for finding in file_findings:
                        row = [
                            finding.get('rule_id', ''),
                            finding.get('severity', ''),
                            finding.get('line', ''),
                            finding.get('column', ''),
                            finding.get('message', ''),
                            finding.get('file_path', '')
                        ]
                        ws.append(row)
                        
                        # Color code by severity
                        severity_colors = {
                            "SEVERE": "FFCCCC",    # Light red
                            "WARNING": "FFFFCC",  # Light yellow
                            "INFO": "CCE5FF",     # Light blue
                            "HINT": "E6FFE6"      # Light green
                        }
                        
                        severity = finding.get('severity', '')
                        if severity in severity_colors:
                            fill = PatternFill(start_color=severity_colors[severity], 
                                             end_color=severity_colors[severity], 
                                             fill_type="solid")
                            for col_num in range(1, len(headers) + 1):
                                ws.cell(row=ws.max_row, column=col_num).fill = fill
                    
                    # Auto-adjust column widths
                    for column in ws.columns:
                        max_length = 0
                        column_letter = get_column_letter(column[0].column)
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)  # Cap at 50
                        ws.column_dimensions[column_letter].width = adjusted_width
                    
                    # Update summary sheet
                    file_severe_count = len([f for f in file_findings if f.get('severity') == 'SEVERE'])
                    file_warning_count = len([f for f in file_findings if f.get('severity') == 'WARNING'])
                    file_info_count = len([f for f in file_findings if f.get('severity') == 'INFO'])
                    summary_sheet.append([file_path, len(file_findings), file_severe_count, file_warning_count, file_info_count])
                
                # Save to bytes
                import io
                output = io.BytesIO()
                wb.save(output)
                excel_data = output.getvalue()
                
            except ImportError:
                # If openpyxl isn't available, create a simple CSV
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
                # Change content type to CSV if openpyxl not available
                self.send_header('Content-type', 'text/csv')
                self.send_header('Content-Disposition', 'attachment; filename="arcane-auditor-results.csv"')
                self.end_headers()
                self.wfile.write(excel_data)
                return
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            self.send_header('Content-Disposition', 'attachment; filename="arcane-auditor-results.xlsx"')
            self.end_headers()
            self.wfile.write(excel_data)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Excel download error: {str(e)}")
            print(f"Traceback: {error_details}")
            self.send_error(500, f"Download failed: {str(e)}")
    
    def handle_get_rules(self):
        """Handle get rules request."""
        try:
            # Try direct import first
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
            # If direct import fails, try uv run as fallback
            try:
                import subprocess
                
                # Use proper path escaping for Windows
                project_root_str = str(project_root).replace('\\', '\\\\')
                
                result = subprocess.run([
                    'uv', 'run', 'python', '-c', f'''
import sys
sys.path.insert(0, r"{project_root_str}")
from parser.rules_engine import RulesEngine
import json

rules_engine = RulesEngine()
rules = rules_engine.get_all_rules()

rules_data = [
    {{
        "name": rule.__class__.__name__,
        "description": getattr(rule, "description", "No description available"),
        "enabled": rule.__class__.__name__ in rules_engine.get_enabled_rules(),
        "severity": "default"
    }}
    for rule in rules
]

print(json.dumps({{"rules": rules_data}}))
'''
                ], capture_output=True, text=True, cwd=project_root)
                
                if result.returncode == 0:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(result.stdout.encode())
                    return
                    
            except (FileNotFoundError, subprocess.SubprocessError) as e:
                # uv not available
                self.send_error(500, f"Rules retrieval failed: uv run not available: {str(e)}")
                return
            
        except Exception as e:
            # Any other error
            self.send_error(500, f"Rules retrieval failed: {str(e)}")
            return
    
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
