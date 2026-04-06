"""Setup script for dmapagent."""
import os
import sys
from pathlib import Path

def setup():
    """Setup dmapagent project."""
    print("Setting up Data Mapping Agent (dmapagent)...")
    print()
    
    # Check Python version
    if sys.version_info < (3, 12):
        print(f"⚠ Warning: dmapagent requires Python 3.12+, you have {sys.version}")
        print("Please upgrade Python to use this project.")
        sys.exit(1)
    
    print("✓ Python version OK")
    
    # Create necessary directories
    dirs = [
        "examples/output",
        "test_data",
    ]
    
    for dir_name in dirs:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_name}")
    
    # Create .env template if it doesn't exist
    env_file = ".env"
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write("""# Data Mapping Agent Configuration

# Google Gemini API Key (Primary LLM)
# Get from: https://aistudio.google.com
GOOGLE_API_KEY=

# Anthropic Claude API Key (Fallback 1)
# Get from: https://console.anthropic.com
ANTHROPIC_API_KEY=

# Ollama Configuration (Fallback 2)
# Ensure Ollama is running: https://ollama.ai
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2

# LLM Parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
LLM_TIMEOUT=60

# Logging
LOG_LEVEL=INFO

# Processing
DEFAULT_ENCODING=utf-8
MAX_DOCUMENT_SIZE_MB=100
""")
        print(f"✓ Created template: {env_file}")
    else:
        print(f"ℹ {env_file} already exists (not overwritten)")
    
    print()
    print("Setup complete!")
    print()
    print("Next steps:")
    print("1. Edit .env file and add your API keys (optional)")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run examples: python examples/simple_1_to_1.py")
    print("4. Try CLI: python main.py --help")
    print()
    print("Documentation: See README.md and docs/ folder")

if __name__ == "__main__":
    setup()
