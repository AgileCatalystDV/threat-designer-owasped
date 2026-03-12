import os
import json
from langgraph.checkpoint.memory import MemorySaver
from typing import Optional, Any

# Try to import OpenAI support (used for both real OpenAI and Ollama)
try:
    from langchain_openai import ChatOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    ChatOpenAI = None

# Environment Configuration
MODEL_ID = os.environ.get("MODEL_ID")
S3_BUCKET = os.environ.get("S3_BUCKET", os.environ.get("ARCHITECTURE_BUCKET", "threat-designer-bucket"))
REGION = os.environ.get("REGION", "us-east-1")
MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "ollama")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
INFERENCE_BASE_URL = os.environ.get("INFERENCE_BASE_URL", "http://localhost:11434/v1")
INFERENCE_API_KEY = os.environ.get("INFERENCE_API_KEY", "ollama")
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "qwen3:32b")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "8192"))

# Tavily Configuration
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")


def _parse_reasoning_config() -> dict:
    """Parse reasoning budget (Bedrock) or effort (OpenAI) from environment"""
    if MODEL_PROVIDER == "openai":
        raw = os.environ.get(
            "REASONING_EFFORT", '{"0": "none", "1": "low", "2": "medium", "3": "high"}'
        )
        return {int(k): v for k, v in json.loads(raw).items()}
    else:
        raw = os.environ.get("REASONING_BUDGET", '{"1": 16000, "2": 32000, "3": 63999}')
        return {int(k): int(v) for k, v in json.loads(raw).items()}


REASONING_CONFIG = _parse_reasoning_config()

ADAPTIVE_THINKING_MODELS = json.loads(os.environ.get("ADAPTIVE_THINKING_MODELS", "[]"))
ADAPTIVE_EFFORT_MAP = {1: "low", 2: "medium", 3: "high", 4: "max"}
OPENAI_REASONING_EFFORT_MAP = {0: "none", 1: "low", 2: "medium", 3: "high"}

# LangGraph checkpointer — MemorySaver keeps conversation state in-process.
# Sessions survive requests (the agent is a long-lived singleton) but reset on restart.
checkpointer = MemorySaver()

# boto_client placeholder — passed to get_or_create_agent() but not used by Ollama/OpenAI path.
# Only needed for Bedrock multimodal diagram fetching.
boto_client = None

# Available Tools (populated during lifespan startup)
ALL_AVAILABLE_TOOLS = []

BUDGET_MAPPING = {1: 16000, 2: 32000, 3: 63999}


def _create_ollama_model_config(budget_level: int = 1) -> dict:
    """Create ChatOpenAI config pointing at Ollama's OpenAI-compatible API."""
    return {
        "model": LOCAL_MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": 0,
        "api_key": INFERENCE_API_KEY,
        "base_url": INFERENCE_BASE_URL,
        # No use_responses_api — not supported by Ollama
    }


def _create_openai_model_config(budget_level: int = 1) -> dict:
    """Create OpenAI model configuration based on budget level."""
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "OpenAI provider requires langchain-openai. Install with: pip install langchain-openai"
        )
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    base_config = {
        "model": MODEL_ID or "gpt-4o",
        "max_tokens": MAX_TOKENS,
        "api_key": OPENAI_API_KEY,
        "temperature": 0,
        "use_responses_api": True,
        "streaming": True,
    }

    if budget_level > 0:
        reasoning_effort = REASONING_CONFIG.get(budget_level, "low")
        base_config["reasoning"] = {"effort": reasoning_effort, "summary": "detailed"}

    return base_config


def _create_bedrock_model_config(budget_level: int = 1) -> dict:
    """Create Bedrock model configuration based on budget level."""
    from botocore.config import Config
    import boto3

    bedrock_client = boto3.client(
        "bedrock-runtime",
        region_name=REGION,
        config=Config(read_timeout=1000),
    )

    base_config = {
        "max_tokens": MAX_TOKENS,
        "model_id": MODEL_ID,
        "client": bedrock_client,
        "temperature": 0 if budget_level == 0 else 1,
    }

    if budget_level == 0:
        return base_config

    if MODEL_ID in ADAPTIVE_THINKING_MODELS:
        effort = ADAPTIVE_EFFORT_MAP.get(budget_level, "low")
        base_config["additional_model_request_fields"] = {
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": effort},
        }
    else:
        budget_tokens = REASONING_CONFIG.get(budget_level, REASONING_CONFIG.get(3, 8000))
        base_config["additional_model_request_fields"] = {
            "thinking": {"type": "enabled", "budget_tokens": budget_tokens},
            "anthropic_beta": ["interleaved-thinking-2025-05-14"],
        }

    return base_config


def create_model_config(budget_level: int = 1) -> dict:
    """Create model configuration based on budget level and provider."""
    if MODEL_PROVIDER == "ollama":
        return _create_ollama_model_config(budget_level)
    elif MODEL_PROVIDER == "openai":
        return _create_openai_model_config(budget_level)
    else:
        return _create_bedrock_model_config(budget_level)


def create_model(budget_level: int = 1) -> Any:
    """Create model instance based on provider."""
    config = create_model_config(budget_level)

    if MODEL_PROVIDER in ("ollama", "openai"):
        return ChatOpenAI(**config)
    else:
        from langchain_aws import ChatBedrockConverse

        return ChatBedrockConverse(**config)
