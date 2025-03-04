#!/usr/bin/env python3
"""
Repository Documentation Pipeline

Processes a directory of zipped repositories, generating documentation for each one.
"""

import os
import sys
import subprocess
import tempfile
import zipfile
from pathlib import Path

def process_repositories(zip_directory: str, output_directory: str, llm_type: str = 'claude'):
    """
    Process all repository zip files and generate documentation.
    
    Args:
        zip_directory: Directory containing repository zip files
        output_directory: Directory where documentation files will be saved
    """
    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)
    
    # Map LLM type to environment variable
    env_var_map = {
        'claude': 'ANTHROPIC_API_KEY',
        'gemini': 'GOOGLE_API_KEY',
        'openai': 'OPENAI_API_KEY'
    }
    
    # Get API key from environment
    env_var = env_var_map.get(llm_type.lower())
    if not env_var:
        raise ValueError(f"Invalid LLM type: {llm_type}. Must be one of: {list(env_var_map.keys())}")
    
    api_key = os.environ.get(env_var)
    if not api_key:
        raise ValueError(f"{env_var} environment variable not set")
    
    # Process each repository
    for zip_name in os.listdir(zip_directory):
        if not zip_name.endswith('.zip'):
            continue
            
        zip_path = os.path.join(zip_directory, zip_name)
        try:
            # Extract zip to temp directory
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_path = os.path.join(temp_dir, f"repo_{zip_name[:-4]}")
                
                # Extract zip file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(repo_path)
                # Generate output filename from zip name
                output_name = os.path.splitext(zip_name)[0] + '_doc.md'
                output_path = os.path.join(output_directory, output_name)
                
                print(f"\nProcessing {zip_name}...")
                print(f"Documentation will be saved to: {output_path}")
                
                # Generate documentation using repo_doc.py
                subprocess.run([
                    sys.executable,
                    os.path.join(os.path.dirname(__file__), 'repo_doc.py'),
                    repo_path,
                    output_path,
                    llm_type
                ], check=True, env={env_var: api_key, **os.environ})
                print(f"Successfully documented {zip_name}")
                
        except Exception as e:
            print(f"Error processing {zip_name}: {e}")
            continue

def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: process_repos.py <zip_directory> <output_directory> [llm_type]")
        sys.exit(1)
    
    zip_directory = sys.argv[1]
    output_directory = sys.argv[2]
    llm_type = sys.argv[3] if len(sys.argv) > 3 else 'claude'
    
    try:
        process_repositories(zip_directory, output_directory, llm_type)
        print("\nAll repositories processed!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
