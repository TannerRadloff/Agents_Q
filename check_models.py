"""
This script analyzes all Python files in the project to detect any
Pydantic model classes with default values that could cause issues with the OpenAI Responses API.
"""

import os
import re
import sys
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

# Regular expressions for detecting Pydantic model class definitions and attributes with default values
CLASS_PATTERN = r'class\s+(\w+)\s*\(\s*BaseModel\s*\)'
FIELD_PATTERN = r'(\w+)\s*:\s*(?:Optional\[)?(\w+)(?:\])?\s*=\s*(?!Field\(default_factory)(.*?)$'

# List of directories to ignore
IGNORE_DIRS = ['.git', 'venv', '__pycache__', '.vscode']

def scan_file(file_path):
    """Scan a Python file for Pydantic model classes with default values."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if this is a Python file that imports BaseModel
        if 'BaseModel' not in content:
            return []
            
        lines = content.split('\n')
        current_class = None
        
        for i, line in enumerate(lines):
            # Check for class definition
            class_match = re.search(CLASS_PATTERN, line)
            if class_match:
                current_class = class_match.group(1)
                continue
                
            # Check for field with default value
            if current_class:
                field_match = re.search(FIELD_PATTERN, line)
                if field_match:
                    field_name = field_match.group(1)
                    field_type = field_match.group(2)
                    default_value = field_match.group(3).strip()
                    
                    # Skip if the default is None (Optional fields are fine)
                    if default_value == 'None':
                        continue
                        
                    # Skip if the default is using Field(default_factory=...)
                    if 'Field(default_factory=' in line:
                        continue
                        
                    issues.append({
                        'file': file_path,
                        'line': i + 1,
                        'class': current_class,
                        'field': field_name,
                        'type': field_type,
                        'default': default_value,
                        'content': line.strip()
                    })
                
                # Check if we're leaving the class definition (indentation changes)
                elif line and not line.startswith(' ') and not line.startswith('\t'):
                    current_class = None
                    
    except Exception as e:
        print(f"Error scanning {file_path}: {e}")
    
    return issues

def scan_directory(directory):
    """Recursively scan a directory for Python files with Pydantic models."""
    issues = []
    
    for root, dirs, files in os.walk(directory):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                file_issues = scan_file(file_path)
                issues.extend(file_issues)
    
    return issues

def main():
    # Determine the base directory to scan
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = '.'
    
    print(f"Scanning for Pydantic models with default values in {base_dir}...")
    issues = scan_directory(base_dir)
    
    if not issues:
        print(f"\n{Fore.GREEN}✓ No problematic default values found in Pydantic models.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}Found {len(issues)} potential issues:{Style.RESET_ALL}")
        
        last_file = None
        for issue in sorted(issues, key=lambda x: (x['file'], x['line'])):
            if issue['file'] != last_file:
                print(f"\n{Fore.CYAN}{issue['file']}{Style.RESET_ALL}")
                last_file = issue['file']
            
            print(f"  Line {issue['line']}: Class {Fore.YELLOW}{issue['class']}{Style.RESET_ALL}, Field {Fore.YELLOW}{issue['field']}{Style.RESET_ALL} = {issue['default']}")
            print(f"    {Fore.WHITE}{issue['content']}{Style.RESET_ALL}")
            print(f"    {Fore.GREEN}-> Suggestion: Change to Optional[{issue['type']}] = None or use Field(default_factory=...){Style.RESET_ALL}")
    
    return len(issues)

if __name__ == "__main__":
    sys.exit(main()) 