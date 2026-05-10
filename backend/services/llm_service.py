import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=False)

DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324"

class LLMConfigurationError(RuntimeError):
    pass

class LLMInvocationError(RuntimeError):
    pass

def get_env(name, default=None):
    return os.getenv(name, default)

def is_llm_configured():
    return bool(os.getenv("OPENAI_API_KEY"))

def get_chat_llm(temperature=0):
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

    if not api_key:
        raise LLMConfigurationError(
            "OPENAI_API_KEY is not configured. Running deterministic fallback instead."
        )

    try:
        from langchain_openai import ChatOpenAI
    except Exception as error:
        raise LLMConfigurationError(
            f"langchain-openai is not installed or could not import: {type(error).__name__}: {error}"
        ) from error

    kwargs = {
        "model": model,
        "temperature": temperature,
        "api_key": api_key,
        "timeout": float(os.getenv("OPENAI_TIMEOUT", "20")),
        "max_retries": int(os.getenv("OPENAI_MAX_RETRIES", "0")),
    }
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)

def invoke_text_prompt(template, values, temperature=0, fallback=None):
    if not is_llm_configured():
        if fallback is not None:
            return fallback()
        raise LLMConfigurationError("OPENAI_API_KEY is not configured.")
    try:
        from langchain_core.prompts import ChatPromptTemplate
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | get_chat_llm(temperature=temperature)
        response = chain.invoke(values)
        return response.content
    except Exception as error:
        if fallback is not None:
            return fallback()
        raise LLMInvocationError(f"LLM request failed: {type(error).__name__}: {error}") from error

# Backwards-compatible helper for any older code passing a LangChain prompt object.
def invoke_prompt(prompt, values, temperature=0, fallback=None):
    if not is_llm_configured():
        if fallback is not None:
            return fallback()
        raise LLMConfigurationError("OPENAI_API_KEY is not configured.")
    try:
        chain = prompt | get_chat_llm(temperature=temperature)
        response = chain.invoke(values)
        return response.content
    except Exception as error:
        if fallback is not None:
            return fallback()
        raise LLMInvocationError(f"LLM request failed: {type(error).__name__}: {error}") from error
