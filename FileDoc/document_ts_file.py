import streamlit as st
import tiktoken
import os
from typing import Optional
import json
import tempfile
import asyncio
from openai import AsyncOpenAI
from db_helper import AnalyticsDB

# Initialize analytics DB with environment-aware path
db_path = os.getenv('DB_PATH', 'analytics.db')
db = AnalyticsDB(db_path)

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
    enc = tiktoken.encoding_for_model("gpt-4")
    return len(enc.encode(text))

async def call_llm_api(prompt: str) -> tuple[str, int, int]:
    """Call the OpenAI Chat API to generate documentation. Returns (response, prompt_tokens, completion_tokens)"""
    client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {"role": "system", "content": "You are a TypeScript documentation expert who writes clear, helpful documentation for junior developers with 1-4 years experience."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        
        return response.choices[0].message.content, prompt_tokens, completion_tokens
    except Exception as e:
        st.error(f"Error calling LLM API: {str(e)}")
        return None, 0, 0

def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate cost in USD based on GPT-4 Turbo pricing."""
    prompt_cost = (prompt_tokens / 1000) * 0.0025
    completion_cost = (completion_tokens / 1000) * 0.01
    return prompt_cost + completion_cost

async def process_file_async(file_obj) -> tuple[Optional[str], Optional[str], str]:
    """Process the uploaded file asynchronously."""
    try:
        code = file_obj.getvalue().decode('utf-8')
        file_size = len(code)
        
        prompt = create_documentation_prompt(code)
        documented_code, prompt_tokens, completion_tokens = await call_llm_api(prompt)
        
        # Calculate and format token usage and cost
        total_tokens = prompt_tokens + completion_tokens
        cost = calculate_cost(prompt_tokens, completion_tokens)
        usage_msg = f"Token usage: {prompt_tokens} prompt + {completion_tokens} completion = {total_tokens} total\nEstimated cost: ${cost:.4f}"
        
        # Store metrics in session state for later use
        st.session_state.file_metrics = {
            'file_size': file_size,
            'token_count': total_tokens,
            'cost': cost,
            'filename': file_obj.name
        }
        
        return code, documented_code, usage_msg
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None, None, f"Error: {str(e)}"

def save_documented_code(documented_code: str, feedback: str, filename: str) -> tuple[bool, str]:
    """Save the documented code and return status."""
    try:
        if not documented_code:
            return False, "No documented code to save"
        
        if not filename.strip():
            filename = "documented_code.ts"
        elif not filename.endswith(('.ts', '.tsx')):
            filename = filename + '.ts'
        
        # Log the operation with all information including feedback
        if 'file_metrics' in st.session_state:
            metrics = st.session_state.file_metrics
            db.log_operation(
                source_file=metrics['filename'],
                file_size=metrics['file_size'],
                token_count=metrics['token_count'],
                estimated_cost=metrics['cost'],
                user_feedback=feedback
            )
        
        return True, documented_code
    except Exception as e:
        return False, str(e)

def main():
    st.set_page_config(page_title="Sharpen TS FileDoc", layout="wide")
    
    # Custom CSS
    st.markdown("""
        <style>
        .stApp > header {
            background-color: transparent;
        }
        .main .block-container {
            padding-top: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Header
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.image("static/Sharpen_Logo.png", width=150)
    with col2:
        st.title("TS File Documenter")
    
    # File upload
    uploaded_file = st.file_uploader("Upload TypeScript File", type=['ts', 'tsx'])
    
    if uploaded_file:
        # Process file
        if 'original_code' not in st.session_state:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            original, documented, usage = loop.run_until_complete(process_file_async(uploaded_file))
            loop.close()
            
            if original and documented:
                st.session_state.original_code = original
                st.session_state.documented_code = documented
                st.session_state.usage = usage
    
    # Display results if available
    if 'original_code' in st.session_state:
        col1, col2 = st.columns(2)
        with col1:
            st.text_area("Original Code", st.session_state.original_code, height=400)
        with col2:
            documented_code = st.text_area("Documented Code (Edit if needed)", 
                                         st.session_state.documented_code, 
                                         height=400)
        
        st.text(st.session_state.usage)
        
        feedback = st.text_area("If you edited the documentation, please explain why and how the AI could improve",
                              height=100)
        
        filename = st.text_input("Save As (optional)", "documented_code.ts")
        
        if st.button("Save and Download"):
            success, result = save_documented_code(documented_code, feedback, filename)
            if success:
                st.download_button(
                    label="Download Documented Code",
                    data=result,
                    file_name=filename,
                    mime="text/plain"
                )
            else:
                st.error(f"Error saving file: {result}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    import logging
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    load_dotenv()
    
    if not os.getenv('OPENAI_API_KEY'):
        logger.error("Error: OPENAI_API_KEY environment variable not set")
        st.error("Error: OPENAI_API_KEY environment variable not set")
    else:
        main()
