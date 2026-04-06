"""Multi-LLM provider with fallback chain (Gemini > Claude > Ollama)."""
import os
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

settings = get_settings()


class LLMBase(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def invoke(self, prompt: str, **kwargs) -> str:
        """Invoke LLM with prompt."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if LLM is available."""
        pass


class GeminiLLM(LLMBase):
    """Google Gemini LLM provider."""

    def __init__(self):
        """Initialize Gemini LLM."""
        self.api_key = os.getenv("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY
        self.client = None
        if self.is_available():
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai
                logger.info("Initialized Gemini LLM")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.client = None

    def is_available(self) -> bool:
        """Check if Gemini API key is available."""
        return bool(self.api_key) and self.client is not None

    def invoke(self, prompt: str, **kwargs) -> str:
        """Invoke Gemini model."""
        if not self.is_available():
            raise RuntimeError("Gemini LLM not available")

        try:
            model = self.client.GenerativeModel("gemini-pro")
            response = model.generate_content(
                prompt,
                generation_config=self.client.types.GenerationConfig(
                    temperature=kwargs.get("temperature", settings.LLM_TEMPERATURE),
                    max_output_tokens=kwargs.get("max_tokens", settings.LLM_MAX_TOKENS),
                ),
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini invocation failed: {e}")
            raise


class ClaudeLLM(LLMBase):
    """Anthropic Claude LLM provider."""

    def __init__(self):
        """Initialize Claude LLM."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY") or settings.ANTHROPIC_API_KEY
        self.client = None
        if self.is_available():
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Initialized Claude LLM")
            except Exception as e:
                logger.error(f"Failed to initialize Claude: {e}")
                self.client = None

    def is_available(self) -> bool:
        """Check if Claude API key is available."""
        return bool(self.api_key) and self.client is not None

    def invoke(self, prompt: str, **kwargs) -> str:
        """Invoke Claude model."""
        if not self.is_available():
            raise RuntimeError("Claude LLM not available")

        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=kwargs.get("max_tokens", settings.LLM_MAX_TOKENS),
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude invocation failed: {e}")
            raise


class OllamaLLM(LLMBase):
    """Ollama local LLM provider (Gemma2)."""

    def __init__(self):
        """Initialize Ollama LLM."""
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.client = None
        if self.is_available():
            try:
                import ollama
                self.client = ollama
                logger.info(f"Initialized Ollama LLM ({self.model})")
            except Exception as e:
                logger.error(f"Failed to initialize Ollama: {e}")
                self.client = None

    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        if not self.client:
            return False

        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    def invoke(self, prompt: str, **kwargs) -> str:
        """Invoke Ollama model."""
        if not self.is_available():
            raise RuntimeError("Ollama LLM not available")

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
                options={
                    "temperature": kwargs.get("temperature", settings.LLM_TEMPERATURE),
                    "num_predict": kwargs.get("max_tokens", settings.LLM_MAX_TOKENS),
                },
            )
            return response["response"]
        except Exception as e:
            logger.error(f"Ollama invocation failed: {e}")
            raise


class LLMProvider:
    """Multi-LLM provider with automatic fallback."""

    def __init__(self):
        """Initialize provider with fallback chain."""
        self.llms = []
        self.current_llm: Optional[LLMBase] = None

        # Initialize all LLMs in priority order
        self.gemini = GeminiLLM()
        if self.gemini.is_available():
            self.llms.append(("Gemini", self.gemini))
            logger.info("Gemini available")

        self.claude = ClaudeLLM()
        if self.claude.is_available():
            self.llms.append(("Claude", self.claude))
            logger.info("Claude available")

        self.ollama = OllamaLLM()
        if self.ollama.is_available():
            self.llms.append(("Ollama", self.ollama))
            logger.info("Ollama available")

        if not self.llms:
            raise RuntimeError(
                "No LLM providers available. Please set GOOGLE_API_KEY, ANTHROPIC_API_KEY, "
                "or ensure Ollama is running."
            )

        self.current_llm = self.llms[0][1]
        logger.info(f"Using primary LLM: {self.llms[0][0]}")

    def invoke(self, prompt: str, **kwargs) -> str:
        """Invoke LLM with automatic fallback on failure."""
        for llm_name, llm in self.llms:
            try:
                logger.debug(f"Attempting invocation with {llm_name}")
                response = llm.invoke(prompt, **kwargs)
                self.current_llm = llm
                return response
            except Exception as e:
                logger.warning(f"{llm_name} failed: {e}, trying next LLM...")
                continue

        raise RuntimeError("All LLM providers failed")

    def get_available_llms(self) -> list:
        """Get list of available LLM names."""
        return [name for name, _ in self.llms]

    def get_current_llm_name(self) -> str:
        """Get current LLM name."""
        for name, llm in self.llms:
            if llm == self.current_llm:
                return name
        return "Unknown"


def get_llm_provider() -> LLMProvider:
    """Get LLM provider instance."""
    return LLMProvider()
