"""
Output formatting module for Arcane Auditor.
Provides various output formats with emojis and better formatting.
"""
from typing import List, Dict
from pathlib import Path
import json
from enum import Enum

from parser.rules.base import Finding


class OutputFormat(Enum):
    """Available output formats."""
    CONSOLE = "console"
    JSON = "json"
    SUMMARY = "summary"
    EXCEL = "excel"


class OutputFormatter:
    """Formats analysis results for different output types."""
    
    # Emoji mappings for different severity levels
    SEVERITY_EMOJIS = {
        "SEVERE": "🔴",
        "WARNING": "🟡", 
        "INFO": "🔵",
        "HINT": "💡"
    }
    
    # Emoji mappings for different rule categories
    RULE_CATEGORY_EMOJIS = {
        "SCRIPT": "📝",
        "STRUCT": "🏗️",
        "STYLE": "🎨",
        "CUSTOM": "⚙️"
    }
    
    def __init__(self, format_type: OutputFormat = OutputFormat.CONSOLE):
        self.format_type = format_type
    
    def format_results(self, findings: List[Finding], total_files: int = 0, total_rules: int = 0) -> str:
        """Format analysis results based on the selected format."""
        if self.format_type == OutputFormat.JSON:
            return self._format_json(findings, total_files, total_rules)
        elif self.format_type == OutputFormat.SUMMARY:
            return self._format_summary(findings, total_files, total_rules)
        elif self.format_type == OutputFormat.EXCEL:
            return self._format_excel(findings, total_files, total_rules)
        else:
            return self._format_console(findings, total_files, total_rules)
    
    def _format_console(self, findings: List[Finding], total_files: int, total_rules: int) -> str:
        """Format results for console output with emojis and better formatting."""
        output = []
        
        # Header with emojis
        output.append("🔮 **Arcane Auditor Analysis Results**")
        output.append("=" * 50)
        
        # Summary statistics
        if total_files > 0 or total_rules > 0:
            output.append(f"📊 **Analysis Summary:**")
            output.append(f"   📁 Files analyzed: {total_files}")
            output.append(f"   🔍 Rules executed: {total_rules}")
            output.append(f"   ⚠️  Issues found: {len(findings)}")
            output.append("")
        
        if not findings:
            output.append("✅ **No issues found!** Your code looks great!")
            return "\n".join(output)
        
        # Group findings by file
        findings_by_file = self._group_findings_by_file(findings)
        
        output.append(f"🚨 **Found {len(findings)} issue(s):**")
        output.append("")
        
        for file_path, file_findings in findings_by_file.items():
            # File header with emoji
            output.append(f"📄 **{file_path}**")
            output.append("-" * (len(file_path) + 4))
            
            # Group findings by severity within each file
            severity_groups = self._group_findings_by_severity(file_findings)
            
            for severity, severity_findings in severity_groups.items():
                emoji = self.SEVERITY_EMOJIS.get(severity, "❓")
                output.append(f"  {emoji} **{severity}** ({len(severity_findings)} issue(s))")
                
                for finding in severity_findings:
                    # Rule category emoji
                    rule_category = finding.rule_id.split('0')[0] if '0' in finding.rule_id else "UNKNOWN"
                    category_emoji = self.RULE_CATEGORY_EMOJIS.get(rule_category, "🔧")
                    
                    # Format the finding with file path
                    file_display = finding.file_path.split('\\')[-1] if finding.file_path else "Unknown"
                    output.append(f"    {category_emoji} **[{finding.rule_id}:{finding.line}]** in `{file_display}`: {finding.message}")
            
            output.append("")  # Empty line between files
        
        # Footer with helpful message
        output.append("💡 **Tip:** Use `--config` to customize rules or `--help` for more options.")
        
        return "\n".join(output)
    
    def _format_summary(self, findings: List[Finding], total_files: int, total_rules: int) -> str:
        """Format a concise summary of results."""
        output = []
        
        # Quick stats
        severe_count = len([f for f in findings if f.severity == "SEVERE"])
        warning_count = len([f for f in findings if f.severity == "WARNING"])
        info_count = len([f for f in findings if f.severity == "INFO"])
        
        if not findings:
            return "✅ No issues found!"
        
        output.append(f"🔍 Found {len(findings)} issue(s): {severe_count} severe, {warning_count} warnings, {info_count} info")
        
        # Show top 3 issues
        top_findings = findings[:3]
        for finding in top_findings:
            emoji = self.SEVERITY_EMOJIS.get(finding.severity, "❓")
            output.append(f"  {emoji} [{finding.rule_id}] {finding.message}")
        
        if len(findings) > 3:
            output.append(f"  ... and {len(findings) - 3} more")
        
        return "\n".join(output)
    
    def _format_json(self, findings: List[Finding], total_files: int, total_rules: int) -> str:
        """Format results as JSON."""
        result = {
            "summary": {
                "total_files": total_files,
                "total_rules": total_rules,
                "total_findings": len(findings),
                "findings_by_severity": {
                    "SEVERE": len([f for f in findings if f.severity == "SEVERE"]),
                    "WARNING": len([f for f in findings if f.severity == "WARNING"]),
                    "INFO": len([f for f in findings if f.severity == "INFO"])
                }
            },
            "findings": [
                {
                    "rule_id": finding.rule_id,
                    "severity": finding.severity,
                    "message": finding.message,
                    "file_path": finding.file_path,
                    "line": finding.line
                }
                for finding in findings
            ]
        }
        
        return json.dumps(result, indent=2)
    
    def _group_findings_by_file(self, findings: List[Finding]) -> Dict[str, List[Finding]]:
        """Group findings by file path."""
        groups = {}
        for finding in findings:
            file_path = finding.file_path or "Unknown"
            if file_path not in groups:
                groups[file_path] = []
            groups[file_path].append(finding)
        return groups
    
    def _group_findings_by_severity(self, findings: List[Finding]) -> Dict[str, List[Finding]]:
        """Group findings by severity level."""
        groups = {}
        for finding in findings:
            severity = finding.severity
            if severity not in groups:
                groups[severity] = []
            groups[severity].append(finding)
        
        # Sort by severity priority
        severity_order = ["SEVERE", "WARNING", "INFO", "HINT"]
        return {k: groups[k] for k in severity_order if k in groups}
    
    def _format_excel(self, findings: List[Finding], total_files: int, total_rules: int) -> str:
        """Format results as Excel file with separate tabs per file."""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter
        except ImportError:
            return "Error: openpyxl package required for Excel export. Install with: pip install openpyxl"
        
        # Create workbook
        wb = openpyxl.Workbook()
        
        # Remove default sheet
        wb.remove(wb.active)
        
        # Group findings by file
        findings_by_file = self._group_findings_by_file(findings)
        
        # Create summary sheet
        summary_sheet = wb.create_sheet("Summary")
        summary_sheet.append(["Analysis Summary"])
        summary_sheet.append(["Files Analyzed", total_files])
        summary_sheet.append(["Rules Executed", total_rules])
        summary_sheet.append(["Total Issues", len(findings)])
        summary_sheet.append(["Severe", len([f for f in findings if f.severity == "SEVERE"])])
        summary_sheet.append(["Warnings", len([f for f in findings if f.severity == "WARNING"])])
        summary_sheet.append(["Info", len([f for f in findings if f.severity == "INFO"])])
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
            headers = ["Rule ID", "Severity", "Line", "Message"]
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
                    finding.rule_id,
                    finding.severity,
                    finding.line,
                    finding.message
                ]
                ws.append(row)
                
                # Color code by severity
                severity_colors = {
                    "SEVERE": "FFCCCC",    # Light red
                    "WARNING": "FFFFCC",  # Light yellow
                    "INFO": "CCE5FF",     # Light blue
                    "HINT": "E6FFE6"      # Light green
                }
                
                if finding.severity in severity_colors:
                    fill = PatternFill(start_color=severity_colors[finding.severity], 
                                     end_color=severity_colors[finding.severity], 
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
                adjusted_width = min(max_length + 2, 150)  # Cap at 50
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Update summary sheet
            severe_count = len([f for f in file_findings if f.severity == "SEVERE"])
            warning_count = len([f for f in file_findings if f.severity == "WARNING"])
            info_count = len([f for f in file_findings if f.severity == "INFO"])
            summary_sheet.append([file_path, len(file_findings), severe_count, warning_count, info_count])
        
        # Save to temporary file and return path
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        wb.save(temp_file.name)
        temp_file.close()
        
        return temp_file.name
