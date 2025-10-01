"""
PMD Preprocessor for handling multi-line string values.

This module preprocesses PMD files to make them valid JSON by escaping newlines
in all string values while maintaining line number tracking for proper error reporting.
"""
import json
import re
import hashlib
from typing import Dict, List, Tuple


class PMDPreprocessor:
    """Preprocesses PMD files to handle multi-line string values."""

    def preprocess(self, content: str) -> Tuple[str, Dict[str, List[int]], Dict[str, List[List[int]]]]:
        """
        Preprocess PMD content to make it valid JSON using a stateful approach.
        
        Returns:
            Tuple of (processed_content, legacy_line_mappings, hash_to_lines_mapping)
            - processed_content: The preprocessed JSON string
            - legacy_line_mappings: Field name to line numbers (for backward compatibility)
            - hash_to_lines_mapping: Content hash to line numbers (new, precise mapping)
        """
        lines = content.split('\n')
        processed_lines = []
        line_mappings = {}  # Legacy: field name -> lines
        hash_to_lines = {}  # New: content hash -> list of line ranges

        in_multiline_string = False
        multiline_buffer = []
        current_lines = []  # Track lines for the current multiline string
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
                        current_lines = [i + 1]  # Start tracking lines (1-based)

                        # Extract field name for legacy line mapping
                        field_name_match = re.search(r'["\'](.*?)["\']', line_prefix)
                        field_path = field_name_match.group(1) if field_name_match else "unknown"
                        
                        if field_path not in line_mappings:
                           line_mappings[field_path] = []
                        line_mappings[field_path].append(i + 1)
                        continue # Move to the next line
                
                # If it's not a multi-line start, just add the line as is
                processed_lines.append(line)

            else: # We are currently inside a multi-line string
                current_lines.append(i + 1)  # Track this line (1-based)
                line_mappings[field_path].append(i + 1)
                # Check if this line ENDS the multi-line string
                end_match = re.search(r'(.*?)(?<!\\)(")\s*([,]?)\s*$', line)
                if end_match:
                    # This line contains the closing quote
                    in_multiline_string = False
                    multiline_buffer.append(end_match.group(1)) # Content before the quote
                    
                    # Join the content (before escaping for JSON)
                    full_content = '\n'.join(multiline_buffer)
                    
                    # Create hash of the original multiline content
                    content_hash = hashlib.sha256(full_content.encode('utf-8')).hexdigest()
                    
                    # Store hash -> line numbers mapping
                    if content_hash not in hash_to_lines:
                        hash_to_lines[content_hash] = []
                    hash_to_lines[content_hash].append(current_lines.copy())
                    
                    # Now escape for JSON
                    escaped_content = json.dumps(full_content)
                    
                    # Reconstruct the complete, single JSON line
                    closing_suffix = end_match.group(3) # Captures a potential trailing comma
                    final_line = f'{line_prefix}{escaped_content}{closing_suffix}'
                    processed_lines.append(final_line)

                    # Clear the buffers for the next potential multi-line string
                    multiline_buffer = []
                    current_lines = []
                else:
                    # Just another line in the middle of the string, add it to the buffer
                    multiline_buffer.append(line)

        # In case the file ends without closing the string (error handling)
        if in_multiline_string:
            full_content = '\n'.join(multiline_buffer)
            
            # Create hash even for unclosed strings
            content_hash = hashlib.sha256(full_content.encode('utf-8')).hexdigest()
            if content_hash not in hash_to_lines:
                hash_to_lines[content_hash] = []
            hash_to_lines[content_hash].append(current_lines.copy())
            
            escaped_content = json.dumps(full_content)
            final_line = f'{line_prefix}{escaped_content}' # No closing quote
            processed_lines.append(final_line)
        
        # Second pass: hash single-line scripts that weren't caught by multiline logic
        # This ensures ALL script content gets hash mappings
        # Use simpler greedy pattern as suggested - matches field: "value with <% script %>"
        script_pattern = re.compile(r'"[^"]*":\s*"(.*?<%.*?%>.*?)"')
        
        for i, line in enumerate(lines):
            m = script_pattern.search(line)
            if not m:
                continue
            
            raw_value = m.group(1)
            try:
                # Unescape once (because it's still JSON-quoted in the line)
                unescaped = json.loads(f'"{raw_value}"')
            except Exception:
                # Fallback if already clean or has unusual escaping
                unescaped = raw_value
            
            # Create hash using same algorithm as multiline (SHA256 for consistency)
            h = hashlib.sha256(unescaped.encode('utf-8')).hexdigest()
            
            # Only add if not already in mapping (multiline takes precedence)
            if h not in hash_to_lines:
                hash_to_lines[h] = []
            
            # Store as list of lists to match multiline structure
            hash_to_lines[h].append([i + 1])
            
        return '\n'.join(processed_lines), line_mappings, hash_to_lines


def preprocess_pmd_content(content: str) -> Tuple[str, Dict[str, List[int]], Dict[str, List[List[int]]]]:
    """
    Convenience function to preprocess PMD content.
    
    Returns:
        Tuple of (processed_content, legacy_line_mappings, hash_to_lines_mapping)
    """
    preprocessor = PMDPreprocessor()
    return preprocessor.preprocess(content)