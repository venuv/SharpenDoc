#!/usr/bin/env python3
"""
Repository Documentation Generator

Uses gitingest to gather repository content and Anthropic's Claude Sonnet
to generate comprehensive documentation for NodeJS/TS repositories.
"""

import os
import sys
from enum import Enum
from typing import Dict, List, Optional

import anthropic
import google.generativeai as genai
import openai
from gitingest import ingest

DOCUMENTATION_PROMPT = '''You are an expert software documentation specialist tasked with creating comprehensive, practical documentation for a software repository. This documentation is specifically designed for junior to mid-level developers who need to quickly understand and contribute to the codebase, with the goal of minimizing onboarding time in an organization with some turnover.

Here is the full source code of the repository you need to document:

<repository_code>
{code_content}
</repository_code>

Please create detailed documentation based on this code. For each section, follow this process:
1. Work inside <documentation_planning> tags in your thinking block:
   - List out the key components you need to analyze
   - Write a brief summary of each component's role in the system
   - Plan your approach for documenting this section
2. Double-check your statements for accuracy against the provided code
3. Review for conciseness, removing any redundant or unnecessary information
4. Present the final content in markdown format

Create documentation with the following sections:

1. CORE CONCEPTS AND DATA FLOW
   - Identify the primary workflows and data paths
   - Explain the key data structures and their relationships
   - Map out the critical modules and their interactions

2. KEY MODULES WITH IMPLEMENTATION SLICES
   - Identify 3-5 most critical modules by analyzing file sizes and interconnections
   - For each module, extract representative code slices that demonstrate its core functionality
   - Explain the purpose and context of each slice
   - Document common modification patterns for each module

3. INTERACTIVE FLOW DIAGRAMS
   - Create a mermaid.js diagram that shows the main execution paths
   - Highlight decision points and data transformations

4. DEBUGGING COMMON SCENARIOS
   - Document typical failure modes and how to diagnose them
   - Include log patterns to look for and their interpretation
   - Provide step-by-step troubleshooting guides for common issues

5. ENHANCEMENT AND MAINTENANCE GUIDE
   - Provide concrete examples of how to extend the codebase
   - Include code examples for common types of changes (e.g., adding features)
   - Document potential pitfalls and best practices
   - Include any deviations from good practice and suggested fixes for them

6. BUILDING NEW FEATURES
   - Suggest 2-3 potential enhancements with implementation approaches
   - Show integration points for new functionality
   - Provide example code that maintains the project's patterns

Focus on practical, actionable information rather than general descriptions. Include relevant code slices that would help developers understand how the system works. Highlight non-obvious connections between components and implicit assumptions in the code.'''


class LLMType(Enum):
    """Supported LLM types"""
    CLAUDE = "claude"
    GEMINI = "gemini"
    OPENAI = "openai"


class RepoDocumenter:
    """Generates comprehensive documentation for NodeJS/TS repositories."""
    
    # Token limits and chunk sizes for different LLMs
    LLM_CONFIGS = {
        LLMType.CLAUDE: {"chunk_size": 400000, "model": "claude-3-sonnet-20240229"},  # ~100K tokens
        LLMType.GEMINI: {"chunk_size": 800000, "model": "models/gemini-pro"},  # ~200K tokens
        LLMType.OPENAI: {"chunk_size": 200000, "model": "gpt-4-turbo-preview"}  # ~50K tokens
    }
    
    def __init__(self, repo_path: str, api_key: str, llm_type: LLMType = LLMType.CLAUDE):
        """Initialize with repository path, API key, and LLM type."""
        self.repo_path = os.path.abspath(repo_path)
        self.llm_type = llm_type
        self.chunk_size = self.LLM_CONFIGS[llm_type]["chunk_size"]
        
        # Initialize appropriate client
        if llm_type == LLMType.CLAUDE:
            self.client = anthropic.Anthropic(api_key=api_key)
        elif llm_type == LLMType.GEMINI:
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel("gemini-2.0-flash")
        else:  # OpenAI
            self.client = openai.Client(api_key=api_key)
        
        if not os.path.isdir(self.repo_path):
            raise ValueError(f"Directory does not exist: {self.repo_path}")
    
    def gather_repository_content(self) -> str:
        """Gather all code content from the directory."""
        try:
            content_parts = []
            relevant_extensions = ('.js', '.ts', '.tsx', '.jsx', '.json', '.yaml', '.yml', '.md', '.py')
            
            for root, _, files in os.walk(self.repo_path):
                for file in files:
                    if file.endswith(relevant_extensions):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.repo_path)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                content_parts.append(f"\n=== {rel_path} ===\n{content}")
                        except Exception as e:
                            print(f"Warning: Could not read {rel_path}: {e}")
            
            return '\n'.join(content_parts)
        except Exception as e:
            raise RuntimeError(f"Failed to gather directory content: {e}")
    
    def generate_documentation(self) -> str:
        """Generate documentation using the selected LLM."""
        try:
            # Gather repository content
            content = self.gather_repository_content()
            
            # Split content into chunks based on LLM type
            content_chunks = [content[i:i + self.chunk_size] 
                            for i in range(0, len(content), self.chunk_size)]
            
            all_responses = []
            for i, chunk in enumerate(content_chunks, 1):
                print(f"Processing chunk {i} of {len(content_chunks)}...")
                
                # Format the prompt with repository content
                prompt = DOCUMENTATION_PROMPT.format(code_content=chunk)
                if len(content_chunks) > 1:
                    prompt += f"\n\nNOTE: This is part {i} of {len(content_chunks)} of the codebase. Please focus on documenting the code shown in this chunk."
                
                # Generate documentation using appropriate LLM
                if self.llm_type == LLMType.CLAUDE:
                    response = self.client.messages.create(
                        model=self.LLM_CONFIGS[self.llm_type]["model"],
                        max_tokens=4096,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    response_text = response.content[0].text
                
                elif self.llm_type == LLMType.GEMINI:
                    response = self.client.generate_content(prompt)
                    response_text = response.text
                
                else:  # OpenAI
                    response = self.client.chat.completions.create(
                        model=self.LLM_CONFIGS[self.llm_type]["model"],
                        messages=[{"role": "user", "content": prompt}]
                    )
                    response_text = response.choices[0].message.content
                
                all_responses.append(response_text)
            
            # If we had multiple chunks, add a note
            if len(content_chunks) > 1:
                all_responses.insert(0, f"Note: This documentation was generated in {len(content_chunks)} parts due to the size of the codebase.\n\n")
            
            return '\n\n'.join(all_responses)
        except Exception as e:
            raise RuntimeError(f"Failed to generate documentation: {e}")
    
    def save_documentation(self, output_path: str = None):
        """Generate and save documentation to a markdown file."""
        if output_path is None:
            output_path = os.path.join(self.repo_path, 'repo_doc.md')
        
        try:
            documentation = self.generate_documentation()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(documentation)
            
            print(f"Documentation saved to: {output_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to save documentation: {e}")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: repo_doc.py <repository_path> [output_path] [llm_type]")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    llm_type_str = sys.argv[3].lower() if len(sys.argv) > 3 else "claude"
    
    # Map string to LLMType
    try:
        llm_type = LLMType(llm_type_str)
    except ValueError:
        print(f"Error: Invalid LLM type. Must be one of: {[t.value for t in LLMType]}")
        sys.exit(1)
    
    # Get appropriate API key from environment
    env_var_map = {
        LLMType.CLAUDE: "ANTHROPIC_API_KEY",
        LLMType.GEMINI: "GOOGLE_API_KEY",
        LLMType.OPENAI: "OPENAI_API_KEY"
    }
    
    env_var = env_var_map[llm_type]
    api_key = os.environ.get(env_var)
    if not api_key:
        print(f"Error: {env_var} environment variable not set")
        sys.exit(1)
    print(f"Found API key: {api_key[:10]}...")
    
    try:
        documenter = RepoDocumenter(repo_path, api_key, llm_type)
        documenter.save_documentation(output_path)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
