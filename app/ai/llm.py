"""
LLM service.

Handles communication with the local Ollama LLM.
"""

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5"


def generate_response(prompt: str) -> str:
    """
    Send a prompt to Ollama and return the model response.
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]