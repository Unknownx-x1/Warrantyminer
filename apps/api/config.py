import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"

class Settings(BaseSettings):
    PROJECT_NAME: str = "WarrantyPatternMiner"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'warranty_miner.db'}")
    
    # AI / LLM Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    USE_OLLAMA: bool = os.getenv("USE_OLLAMA", "false").lower() in ("true", "1", "yes")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
    
    # Statistical and Clustering Thresholds
    MIN_CLUSTER_SIZE: int = 4
    MIN_SAMPLES: int = 2
    ALERT_SCORE_THRESHOLD: float = 60.0
    CRITICAL_SCORE_THRESHOLD: float = 80.0
    SIGNIFICANCE_Z_THRESHOLD: float = 2.0
    MIN_VOLUME_GUARD: int = 3
    
    # Code Mismatch Configuration
    MISMATCH_HIGH_THRESHOLD: float = 0.70
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# Ensure data folders exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
