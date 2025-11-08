import os

MODEL_NAME = os.getenv("MODEL_NAME", "base")
LANGUAGE_DEFAULT = os.getenv("LANGUAGE_DEFAULT", "ko")
MAX_SECONDS = int(os.getenv("MAX_SECONDS", "60"))
MAX_BYTES = int(os.getenv("MAX_BYTES", "20000000"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")]
API_VERSION = os.getenv("API_VERSION", "v1")
