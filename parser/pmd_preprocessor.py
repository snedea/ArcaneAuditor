"""
PMD Preprocessor for handling multi-line string values.

This module preprocesses PMD files to make them valid JSON by escaping newlines
in all string values while maintaining line number tracking for proper error reporting.
"""
import json
import re
from typing import Dict, List, Tuple


class PMDPreprocessor:
    """Preprocesses PMD files to handle multi-line string values."""

    def preprocess(self, content: str) -> Tuple[str, Dict[str, List[int]]]:
        """
        Preprocess PMD content to make it valid JSON using a stateful approach.
        """
        lines = content.split('\n')
        processed_lines = []
        line_mappings = {}

        in_multiline_string = False
        multiline_buffer = []
        line_prefix = ""
        field_path = ""

        for i, line in enumerate(lines):
            if not in_multiline_string:
                # Check if this line STARTS a multi-line string
                # Pattern: "key": "value... (with no closing quote on the line)
                match = re.match(r'(\s*"[^"]+"\s*:\s*)(")(.*)', line)
                if match:
                    # Check for an unescaped closing quote on the same line
                    content_part = match.group(3)
                    if not re.search(r'(?<!\\)"\s*[,]?\s*$', content_part):
                        # This is the start of a multi-line string
                        in_multiline_string = True
                        line_prefix = match.group(1) # e.g., '  "myKey": '
                        multiline_buffer.append(content_part)

                        # Extract field name for line mapping
                        field_name_match = re.search(r'["\'](.*?)["\']', line_prefix)
                        field_path = field_name_match.group(1) if field_name_match else "unknown"
                        
                        if field_path not in line_mappings:
                           line_mappings[field_path] = []
                        line_mappings[field_path].append(i + 1)
                        continue # Move to the next line
                
                # If it's not a multi-line start, just add the line as is
                processed_lines.append(line)

            else: # We are currently inside a multi-line string
                line_mappings[field_path].append(i + 1)
                # Check if this line ENDS the multi-line string
                end_match = re.search(r'(.*?)(?<!\\)(")\s*([,]?)\s*$', line)
                if end_match:
                    # This line contains the closing quote
                    in_multiline_string = False
                    multiline_buffer.append(end_match.group(1)) # Content before the quote
                    
                    # Join, escape, and format the final line
                    full_content = '\n'.join(multiline_buffer)
                    escaped_content = json.dumps(full_content)
                    
                    # Reconstruct the complete, single JSON line
                    closing_suffix = end_match.group(3) # Captures a potential trailing comma
                    final_line = f'{line_prefix}{escaped_content}{closing_suffix}'
                    processed_lines.append(final_line)

                    # Clear the buffer for the next potential multi-line string
                    multiline_buffer = []
                else:
                    # Just another line in the middle of the string, add it to the buffer
                    multiline_buffer.append(line)

        # In case the file ends without closing the string (error handling)
        if in_multiline_string:
            full_content = '\n'.join(multiline_buffer)
            escaped_content = json.dumps(full_content)
            final_line = f'{line_prefix}{escaped_content}' # No closing quote
            processed_lines.append(final_line)
            
        return '\n'.join(processed_lines), line_mappings


def preprocess_pmd_content(content: str) -> Tuple[str, Dict[str, List[int]]]:
    """
    Convenience function to preprocess PMD content.
    """
    preprocessor = PMDPreprocessor()
    return preprocessor.preprocess(content)