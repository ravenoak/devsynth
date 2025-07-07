#!/usr/bin/env python3

"""
Script to fix inconsistent code block formatting in Markdown files.

Usage:
    python scripts/fix_code_blocks.py

This script:
1. Finds all Markdown files in the docs directory
2. Ensures all code blocks have a language specifier (e.g., ```python, ```bash)
3. Ensures there's a blank line before and after each code block
4. Reports the changes made
"""

import os
import re
from pathlib import Path

def detect_language(code_content):
    """Detect the language of a code block based on its content."""
    # Check for common language patterns
    if re.search(r'^\s*(import|from|def|class)\s', code_content, re.MULTILINE):
        return "python"
    elif re.search(r'^\s*(function|const|let|var|import)\s', code_content, re.MULTILINE):
        return "javascript"
    elif re.search(r'^\s*(package|import|func|type)\s', code_content, re.MULTILINE):
        return "go"
    elif re.search(r'^\s*(#include|int\s+main|void\s+main|std::)', code_content, re.MULTILINE):
        return "cpp"
    elif re.search(r'^\s*(public\s+class|import\s+java|@Override)', code_content, re.MULTILINE):
        return "java"
    elif re.search(r'^\s*(<?php|namespace|use\s+[A-Z])', code_content, re.MULTILINE):
        return "php"
    elif re.search(r'^\s*(#!\s*/bin/bash|apt-get|yum|dnf|echo|cd|mkdir|rm|cp)', code_content, re.MULTILINE):
        return "bash"
    elif re.search(r'^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE TABLE)', code_content, re.IGNORECASE | re.MULTILINE):
        return "sql"
    elif re.search(r'^\s*(<html|<!DOCTYPE|<head|<body|<div|<script)', code_content, re.MULTILINE):
        return "html"
    elif re.search(r'^\s*(body|html|div|span|p)\s*{', code_content, re.MULTILINE):
        return "css"
    elif re.search(r'^\s*(apiVersion|kind|metadata|spec):', code_content, re.MULTILINE):
        return "yaml"
    elif re.search(r'^\s*(\{|\[).*(\}|\])\s*$', code_content, re.MULTILINE):
        return "json"
    
    # Default to text if no pattern matches
    return "text"

def fix_code_blocks(file_path):
    """Fix code block formatting in a Markdown file."""
    changes = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all code blocks
    code_block_pattern = r'```(.*?)\n(.*?)```'
    code_blocks = list(re.finditer(code_block_pattern, content, re.DOTALL))
    
    # Process code blocks in reverse order to avoid index issues
    for match in reversed(code_blocks):
        language = match.group(1).strip()
        code_content = match.group(2)
        start_pos = match.start()
        end_pos = match.end()
        
        # Check if the code block has a language specifier
        if not language:
            # Detect language based on content
            detected_language = detect_language(code_content)
            
            # Replace the code block with one that has a language specifier
            new_code_block = f"```{detected_language}\n{code_content}```"
            content = content[:start_pos] + new_code_block + content[end_pos:]
            changes.append(f"Added language specifier '{detected_language}' to code block")
    
    # Ensure blank lines before and after code blocks
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        if lines[i].startswith('```'):
            # Ensure blank line before code block
            if i > 0 and lines[i-1].strip() != '':
                lines.insert(i, '')
                changes.append("Added blank line before code block")
                i += 1
            
            # Find the end of the code block
            end_index = i + 1
            while end_index < len(lines) and not lines[end_index].startswith('```'):
                end_index += 1
            
            if end_index < len(lines):
                # Ensure blank line after code block
                if end_index + 1 < len(lines) and lines[end_index + 1].strip() != '':
                    lines.insert(end_index + 1, '')
                    changes.append("Added blank line after code block")
                
                i = end_index + 1
            else:
                i += 1
        else:
            i += 1
    
    # Write the fixed content back to the file
    if changes:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    return changes

def main():
    """Main function to fix code block formatting in all Markdown files."""
    docs_dir = Path("docs")
    
    # Find all Markdown files in the docs directory
    md_files = list(docs_dir.glob("**/*.md"))
    print(f"Found {len(md_files)} Markdown files in the docs directory")
    
    # Fix code block formatting in each file
    files_fixed = 0
    for file_path in md_files:
        try:
            changes = fix_code_blocks(file_path)
            if changes:
                print(f"\nFixed {file_path}:")
                for change in changes:
                    print(f"  - {change}")
                files_fixed += 1
        except Exception as e:
            print(f"\nError processing {file_path}: {e}")
    
    print(f"\nFixed code block formatting in {files_fixed} files")

if __name__ == "__main__":
    main()