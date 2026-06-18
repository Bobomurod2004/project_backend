import os
from dotenv import load_dotenv

load_dotenv()

DJANGO_API: str = os.getenv("DJANGO_API", "http://localhost:8001/api")
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "300"))
MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))
NUM_PREDICT: int = int(os.getenv("OLLAMA_NUM_PREDICT", "1800"))
