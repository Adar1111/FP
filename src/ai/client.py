import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def create_ai_client() -> OpenAI:
    # Find the main project folder.
    # This file is located at FP/src/ai/client.py.
    # parents[0] is ai, parents[1] is src, and parents[2] is FP.
    project_root = Path(__file__).resolve().parents[2]

    # Build the full path to the .env file inside FP.
    env_path = project_root / ".env"

    # Read settings from .env into the program's environment.
    load_dotenv(env_path)

    # Get the API key from the environment.
    api_key = os.getenv("OPENAI_API_KEY")

    # Stop with a clear error if the key is missing or empty.
    # This does not check whether the key is valid.
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing from the environment.")

    # Create and return a client for future OpenAI requests.
    # This line does not send a request to the AI model.
    return OpenAI(api_key=api_key)