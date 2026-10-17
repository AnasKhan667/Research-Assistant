import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Central app configuration, sourced from environment variables (.env)."""

    def __init__(self) -> None:
        self.HF_TOKEN: str = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
        self.LLM_REPO_ID: str = os.getenv("LLM_REPO_ID", "Qwen/Qwen2.5-7B-Instruct-Turbo")
        self.LLM_TASK: str = "text-generation"

        self.MAX_NEW_TOKENS: int = int(os.getenv("MAX_NEW_TOKENS", "512"))
        self.TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
        self.TOP_P: float = float(os.getenv("TOP_P", "0.95"))
        self.REPETITION_PENALTY: float = float(os.getenv("REPETITION_PENALTY", "1.15"))

        self.MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "3"))
        self.REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "120"))
        self.MAX_QUERY_LENGTH: int = int(os.getenv("MAX_QUERY_LENGTH", "500"))

        # CORS - comma separated list of allowed origins for the frontend
        self.ALLOWED_ORIGINS: list[str] = os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:3000"
        ).split(",")

    def validate(self) -> None:
        if not self.HF_TOKEN:
            raise ValueError(
                "HUGGINGFACEHUB_API_TOKEN is not set. Add it to backend/.env "
                "(copy backend/.env.example to get started)."
            )
        logger.info("Config validated — HF token is set, model=%s", self.LLM_REPO_ID)


config = Config()
