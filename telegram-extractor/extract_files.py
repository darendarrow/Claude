#!/usr/bin/env python3

"""
Telegram Downloader Files Extractor (Python Version)

This script parses the markdown artifact and extracts all code blocks
into their respective files with proper error handling.

Usage: python3 extract_files.py <markdown_file>
Example: python3 extract_files.py telegram-downloader-files.md
"""

import sys
import os
import re
from pathlib import Path

# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_header():
    """Print script header"""
    print(f"{Colors.BLUE}========================================{Colors.NC}")
    print(f"{Colors.BLUE}Telegram Downloader Files Extractor{Colors.NC}")
    print(f"{Colors.BLUE}========================================{Colors.NC}")
    print()

def parse_markdown(markdown_path):
    """
    Parse markdown file and extract code blocks with their filenames.
    
    Returns:
        List of tuples: [(filename, content), ...]
    """
    with open(markdown_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    files = []
    current_file = None
    in_code_block = False
    code_lines = []
    
    # Pattern to match: ## File: `filename`
    file_pattern = re.compile(r'^##\s+File:\s+`([^`]+)`')
    # Pattern to match code block start/end
    code_block_pattern = re.compile(r'^```[\w]*\s*$')
    
    for line in lines:
        # Check for file header
        file_match = file_pattern.match(line)
        if file_match:
            current_file = file_match.group(1)
            in_code_block = False
            code_lines = []
            continue
        
        # Check for code block delimiter
        if code_block_pattern.match(line) and current_file:
            if not in_code_block:
                # Starting code block
                in_code_block = True
                code_lines = []
            else:
                # Ending code block - save the file
                if code_lines:
                    content = ''.join(code_lines)
                    files.append((current_file, content))
                
                in_code_block = False
                code_lines = []
                current_file = None
            continue
        
        # Accumulate code content
        if in_code_block:
            code_lines.append(line)
    
    return files

def extract_files(markdown_path, output_dir='telegram-downloader'):
    """
    Extract all files from markdown to output directory.
    
    Args:
        markdown_path: Path to markdown file
        output_dir: Directory to extract files to
    """
    print_header()
    print(f"Processing: {Colors.YELLOW}{markdown_path}{Colors.NC}")
    print()
    
    # Check if markdown file exists
    if not os.path.exists(markdown_path):
        print(f"{Colors.RED}Error: File '{markdown_path}' not found{Colors.NC}")
        sys.exit(1)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    print(f"{Colors.GREEN}✓{Colors.NC} Created project directory: {output_dir}")
    print()
    
    # Parse markdown and extract files
    try:
        files = parse_markdown(markdown_path)
    except Exception as e:
        print(f"{Colors.RED}Error parsing markdown: {e}{Colors.NC}")
        sys.exit(1)
    
    # Write files
    extracted_count = 0
    for filename, content in files:
        try:
            file_path = output_path / filename
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(content)
            
            print(f"{Colors.GREEN}✓{Colors.NC} Extracted: {Colors.YELLOW}{filename}{Colors.NC}")
            
            # Make shell scripts executable
            if filename.endswith('.sh'):
                os.chmod(file_path, 0o755)
                print(f"  {Colors.BLUE}→{Colors.NC} Made executable")
            
            extracted_count += 1
            
        except Exception as e:
            print(f"{Colors.RED}✗{Colors.NC} Failed to write {filename}: {e}")
    
    # Print summary
    print()
    print(f"{Colors.BLUE}========================================{Colors.NC}")
    print(f"{Colors.GREEN}Extraction Complete!{Colors.NC}")
    print(f"{Colors.BLUE}========================================{Colors.NC}")
    print(f"Total files extracted: {Colors.GREEN}{extracted_count}{Colors.NC}")
    print(f"Project location: {Colors.YELLOW}{output_path.absolute()}{Colors.NC}")
    print()
    
    # Check for .env.example
    env_example = output_path / '.env.example'
    env_file = output_path / '.env'
    
    if env_example.exists() and not env_file.exists():
        print(f"{Colors.YELLOW}⚠{Colors.NC}  Next steps:")
        print(f"   1. Copy .env.example to .env:")
        print(f"      {Colors.BLUE}cp {output_dir}/.env.example {output_dir}/.env{Colors.NC}")
        print(f"   2. Edit .env and add your Telegram API credentials:")
        print(f"      {Colors.BLUE}nano {output_dir}/.env{Colors.NC}")
        print(f"   3. Get API credentials from: {Colors.BLUE}https://my.telegram.org{Colors.NC}")
        print()
    
    print(f"{Colors.GREEN}✓{Colors.NC} Ready to build and run!")
    print(f"   Next: {Colors.BLUE}cd {output_dir} && docker compose build{Colors.NC}")
    print()

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(f"{Colors.RED}Error: No markdown file specified{Colors.NC}")
        print(f"Usage: {sys.argv[0]} <markdown_file>")
        print(f"Example: {sys.argv[0]} telegram-downloader-files.md")
        sys.exit(1)
    
    markdown_file = sys.argv[1]
    extract_files(markdown_file)

if __name__ == '__main__':
    main()