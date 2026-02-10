"""
LLM Inference Client - Unified interface for different LLM backends.

Supports:
- llama.cpp server (on-premise, production)
- Ollama (easier Windows setup)
- Claude API (development only, NOT for production)
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    backend: str = "claude"  # "llamacpp", "ollama", or "claude"
    base_url: str = "http://localhost:8080"
    model_name: str = "mistral"
    timeout: int = 120


class LLMClient:
    """Unified LLM client - supports llama.cpp, Ollama, or Claude API."""

    def __init__(
        self,
        backend: str = "claude",
        base_url: str = "http://localhost:8080",
        model_name: str = "mistral",
        timeout: int = 120
    ):
        """
        Initialize LLM client.

        Args:
            backend: "llamacpp", "ollama", or "claude"
            base_url: Base URL for llama.cpp or Ollama server
            model_name: Model name for Ollama
            timeout: Request timeout in seconds
        """
        self.backend = backend
        self.base_url = base_url
        self.model_name = model_name
        self.timeout = timeout

        logger.info(f"Initializing LLM client with backend: {backend}")

        # Validate backend-specific requirements
        if backend == "claude":
            if not os.environ.get("ANTHROPIC_API_KEY"):
                logger.warning("ANTHROPIC_API_KEY not set. Claude backend will fail.")

        # Check health
        if not self.health_check():
            logger.warning(f"LLM backend '{backend}' health check failed. Generation may not work.")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.1,
        stop_sequences: Optional[list] = None
    ) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic)
            stop_sequences: Optional list of stop sequences

        Returns:
            Generated text
        """
        logger.debug(f"Generating with {self.backend}: prompt_len={len(prompt)}, max_tokens={max_tokens}")

        if self.backend == "llamacpp":
            return self._llamacpp_generate(prompt, max_tokens, temperature, stop_sequences)
        elif self.backend == "ollama":
            return self._ollama_generate(prompt, max_tokens, temperature, stop_sequences)
        elif self.backend == "claude":
            return self._claude_generate(prompt, max_tokens, temperature, stop_sequences)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def _llamacpp_generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        stop_sequences: Optional[list]
    ) -> str:
        """Generate using llama.cpp server."""
        try:
            payload = {
                "prompt": prompt,
                "n_predict": max_tokens,
                "temperature": temperature,
                "stop": stop_sequences or [],
            }

            response = requests.post(
                f"{self.base_url}/completion",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            return result.get("content", "")

        except Exception as e:
            logger.error(f"llama.cpp generation failed: {e}")
            raise

    def _ollama_generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        stop_sequences: Optional[list]
    ) -> str:
        """Generate using Ollama."""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }

            if stop_sequences:
                payload["options"]["stop"] = stop_sequences

            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    def _claude_generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        stop_sequences: Optional[list]
    ) -> str:
        """
        Generate using Claude API.

        WARNING: This is for DEVELOPMENT ONLY.
        Production must use on-premise llama.cpp or Ollama.
        """
        try:
            import anthropic

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")

            client = anthropic.Anthropic(api_key=api_key)

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                stop_sequences=stop_sequences
            )

            return message.content[0].text

        except Exception as e:
            logger.error(f"Claude API generation failed: {e}")
            raise

    def health_check(self) -> bool:
        """
        Check if LLM backend is available.

        Returns:
            True if backend is healthy, False otherwise
        """
        try:
            if self.backend == "llamacpp":
                response = requests.get(f"{self.base_url}/health", timeout=5)
                return response.status_code == 200

            elif self.backend == "ollama":
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                return response.status_code == 200

            elif self.backend == "claude":
                # Just check if API key is set
                return bool(os.environ.get("ANTHROPIC_API_KEY"))

            return False

        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False


def create_llm_client(backend: str = "claude") -> LLMClient:
    """Factory function to create an LLM client."""
    return LLMClient(backend=backend)


if __name__ == "__main__":
    # Test the client
    logging.basicConfig(level=logging.INFO)

    # Try Claude API (if key is set)
    if os.environ.get("ANTHROPIC_API_KEY"):
        client = create_llm_client(backend="claude")
        print("Testing Claude API...")
        response = client.generate("What is the punishment for murder under Section 302 IPC?", max_tokens=200)
        print(f"Response: {response[:300]}")
    else:
        print("ANTHROPIC_API_KEY not set. Skipping Claude test.")
