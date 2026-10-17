import logging
from typing import Optional

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from app.config import config

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when the LLM endpoint returns an error."""


class LLMManager:
    """Manages interactions with a Hugging Face LLM endpoint via LangChain."""

    def __init__(
        self,
        repo_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_new_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
    ):
        self.repo_id = repo_id or config.LLM_REPO_ID
        self.temperature = (
            temperature if temperature is not None else config.TEMPERATURE
        )
        self.max_new_tokens = max_new_tokens or config.MAX_NEW_TOKENS
        self.top_p = top_p if top_p is not None else config.TOP_P
        self.repetition_penalty = repetition_penalty or config.REPETITION_PENALTY

        self._endpoint = self._build_endpoint()
        self.chat_model = ChatHuggingFace(llm=self._endpoint)
        self.parser = StrOutputParser()

    def _build_endpoint(self) -> HuggingFaceEndpoint:
        logger.info("Connecting to HF endpoint: repo=%s, task=%s", self.repo_id, config.LLM_TASK)
        return HuggingFaceEndpoint(
            repo_id=self.repo_id,
            task=config.LLM_TASK,
            huggingfacehub_api_token=config.HF_TOKEN,
            max_new_tokens=self.max_new_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            repetition_penalty=self.repetition_penalty,
        )

    def invoke(self, messages) -> str:
        """Invoke the chat model with a list of LangChain message objects.

        Raises LLMError on failure so callers can handle it explicitly.
        """
        try:
            response = self.chat_model.invoke(messages)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.exception("LLM invocation failed")
            raise LLMError(f"LLM call failed: {e}") from e

    def chat(self, user_message: str, system_prompt: Optional[str] = None) -> str:
        """Convenience helper - build messages from plain strings and invoke."""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=user_message))
        return self.invoke(messages)
