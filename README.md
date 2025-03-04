# SharpenDoc

SharpenDoc is a toolkit for generating high-quality documentation for your code using AI. It provides two main tools:

## 🔍 FileDoc

FileDoc is a tool for documenting individual TypeScript/JavaScript files. It uses AI to generate comprehensive, developer-friendly documentation that follows best practices.

### Features

- **Web UI**: Upload TS/JS files through a Streamlit interface
- **Documentation Generation**: Adds JSDoc/TypeDoc comments to functions and classes
- **Interactive Editing**: Review, edit, and improve the AI-generated documentation
- **Analytics**: Tracks usage and costs for optimization

### Setup

```bash
cd FileDoc
pip install -r requirements.txt
# Create a .env file with your OpenAI API key
echo "OPENAI_API_KEY=your_key_here" > .env
streamlit run document_ts_file.py
```

## 📚 RepoDoc

RepoDoc is a tool for generating comprehensive documentation for entire repositories, ideal for onboarding new developers.

### Features

- **Comprehensive Analysis**: Analyzes all code in a repository to generate meaningful documentation
- **Multi-LLM Support**: Works with Claude, OpenAI GPT-4, or Google Gemini
- **Chunking**: Handles large codebases by processing in chunks
- **Developer-Oriented**: Focuses on practical information for faster onboarding

### Usage

```bash
cd RepoDoc
pip install -r requirements.txt
# Note: gitingest is required for repository analysis
# Set the appropriate API key in your environment
export ANTHROPIC_API_KEY=your_key_here  # For Claude
# OR
export OPENAI_API_KEY=your_key_here  # For OpenAI
# OR
export GOOGLE_API_KEY=your_key_here  # For Gemini

# Run the documenter
python repo_doc.py /path/to/repository [output_path] [llm_type]
```

## Requirements

- Python 3.8+
- API keys for the LLM of your choice (OpenAI, Anthropic, or Google)
- TypeScript/JavaScript codebase(s) to document

## License

MIT