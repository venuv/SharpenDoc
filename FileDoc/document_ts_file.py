from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import tiktoken
import httpx
import os
from typing import Optional
import json

app = FastAPI()

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

class DocumentationResponse(BaseModel):
    documented_code: str
    token_count: int
    original_code: str

def create_documentation_prompt(code: str) -> str:
    """Creates the prompt for the LLM with specific documentation requirements."""
    return f"""You are a TypeScript documentation expert. Your task is to add comprehensive documentation 
to TypeScript code following Google's documentation standards but adapted for junior developers (1-4 years experience).

Key Requirements:
1. Use TypeDoc/JSDoc format
2. Write in plain language avoiding unnecessary technical jargon
3. Include concrete examples for complex functions
4. Explicitly document error scenarios and edge cases
5. Explain the "why" not just the "what"
6. Add comments for non-obvious code sections

For each function, include:
- A clear description of purpose
- Detailed @param descriptions with types and examples
- @throws documentation with specific error scenarios
- @returns description with example return value
- @example section for complex functions
- Common gotchas or edge cases
- Links to related functions or documentation

Example format:
/**
 * Converts raw client data into our standardized user profile format
 * 
 * Why this exists:
 * - Ensures consistent data format across the application
 * - Validates required fields before database operations
 * - Adds necessary metadata (timestamps, defaults)
 * 
 * @param rawData - The unprocessed data from the client
 *    Expected format: {{ email: string, name?: string }}
 * 
 * @throws {{ValidationError}} 
 *    - When email is missing or invalid
 *    - When name contains invalid characters
 * 
 * @returns Normalized user profile ready for database
 *    Example: {{
 *      email: "user@domain.com",
 *      name: "John Doe",
 *      createdAt: "2024-02-20T..."
 *    }}
 * 
 * @example
 * // Basic usage
 * const profile = await normalizeUserData({{
 *   email: "user@example.com",
 *   name: "John"
 * }});
 * 
 * @see validateEmail - Used internally for email validation
 */
 
Please document the following TypeScript code using these standards:

{code}

Return ONLY the documented code without any additional explanations or markdown formatting."""

async def get_token_count(text: str) -> int:
    """Calculate the number of tokens in the text using tiktoken."""
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    return len(enc.encode(text))

async def call_llm_api(prompt: str) -> str:
    """Call the OpenAI Chat API to generate documentation."""
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a TypeScript documentation expert who writes clear, helpful documentation for junior developers with 1-4 years experience."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent documentation
            max_tokens=4000   # Increased for longer documentation
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/document/", response_model=DocumentationResponse)
async def document_typescript(file: UploadFile = File(...)):
    """
    Process uploaded TypeScript file and return documented version with token count.
    """
    if not file.filename.endswith(('.ts', '.tsx')):
        raise HTTPException(status_code=400, detail="Only TypeScript files are accepted")

    content = await file.read()
    code = content.decode()

    # Create the documentation prompt
    prompt = create_documentation_prompt(code)
    
    # Get token count of original code + prompt
    prompt_tokens = await get_token_count(prompt)
    
    # Get documented code from LLM
    documented_code = await call_llm_api(prompt)
    
    # Get token count of response
    response_tokens = await get_token_count(documented_code)
    
    total_tokens = prompt_tokens + response_tokens

    return DocumentationResponse(
        documented_code=documented_code,
        token_count=total_tokens,
        original_code=code
    )

@app.get("/", response_class=HTMLResponse)
async def get_upload_page():
    """Serve the upload page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TypeScript Documentation Generator</title>
        <style>
            /* Add your CSS styles here */
            .container { max-width: 800px; margin: 0 auto; padding: 20px; }
            .drop-zone { border: 2px dashed #ccc; padding: 20px; text-align: center; }
            .code-display { background: #f5f5f5; padding: 15px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>TypeScript Documentation Generator</h1>
            <div class="drop-zone" id="drop-zone">
                <p>Drag and drop a TypeScript file here or click to upload</p>
                <input type="file" id="file-input" accept=".ts,.tsx" style="display: none;">
            </div>
            <div id="result" style="display: none;">
                <h2>Original Code:</h2>
                <pre class="code-display" id="original-code"></pre>
                <h2>Documented Code:</h2>
                <pre class="code-display" id="documented-code"></pre>
                <p>Total tokens used: <span id="token-count"></span></p>
            </div>
        </div>
        <script>
            // Add your JavaScript for file handling and API calls here
            const dropZone = document.getElementById('drop-zone');
            const fileInput = document.getElementById('file-input');
            
            dropZone.onclick = () => fileInput.click();
            
            dropZone.ondragover = (e) => {
                e.preventDefault();
                dropZone.style.borderColor = '#000';
            };
            
            dropZone.ondragleave = () => {
                dropZone.style.borderColor = '#ccc';
            };
            
            dropZone.ondrop = async (e) => {
                e.preventDefault();
                const file = e.dataTransfer.files[0];
                await processFile(file);
            };
            
            fileInput.onchange = async () => {
                const file = fileInput.files[0];
                await processFile(file);
            };
            
            async function processFile(file) {
                if (!file.name.endsWith('.ts') && !file.name.endsWith('.tsx')) {
                    alert('Please upload a TypeScript file');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/document/', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    document.getElementById('result').style.display = 'block';
                    document.getElementById('original-code').textContent = result.original_code;
                    document.getElementById('documented-code').textContent = result.documented_code;
                    document.getElementById('token-count').textContent = result.token_count;
                } catch (error) {
                    alert('Error processing file: ' + error.message);
                }
            }
        </script>
    </body>
    </html>
    """

# Command line interface
async def process_file(filepath: str) -> None:
    """Process a TypeScript file from command line."""
    try:
        with open(filepath, 'r') as file:
            code = file.read()
            
        # Create the documentation prompt
        prompt = create_documentation_prompt(code)
        
        # Get documented code from LLM
        documented_code = await call_llm_api(prompt)
        
        # Save the documented code
        output_path = filepath.replace('.ts', '_documented.ts')
        with open(output_path, 'w') as file:
            file.write(documented_code)
            
        print(f"\nProcessed successfully!")
        print(f"Original file: {filepath}")
        print(f"Documented file saved to: {output_path}")
        
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    import sys
    import asyncio
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    if len(sys.argv) != 2:
        print("Usage: python main.py <typescript_file>")
        sys.exit(1)
        
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    
    # Get file path from command line argument
    filepath = sys.argv[1]
    
    # Check if file is TypeScript
    if not filepath.endswith(('.ts', '.tsx')):
        print("Error: Please provide a TypeScript file (.ts or .tsx)")
        sys.exit(1)
    
    # Run the async function
    asyncio.run(process_file(filepath))

# To run as web application:
# uvicorn main:app --reload

# Requirements.txt:
"""
fastapi==0.109.2
uvicorn==0.27.1
python-multipart==0.0.9
httpx==0.26.0
anthropic==0.8.1
python-dotenv==1.0.1
"""

# Dockerfile:
"""
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
"""

# fly.toml:
"""
app = "ts-documenter"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"

[[services]]
  internal_port = 8080
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = "80"
"""
