import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
# from langchain_ollama import ChatOpenAI

logger = logging.getLogger(__name__)

load_dotenv()
logger.debug("Environment variables loaded from .env file")

def get_fast_model_name() -> str:
    """Retrieve the fast model name from environment or use default.
    
    Used for quick inference tasks like QA generation.
    """
    model_name = os.getenv("FAST_MODEL", "qwen2.5-coder:1.5b")
    logger.debug(f"get_fast_model_name() - returning model: {model_name}")
    return model_name

def get_smart_model_name() -> str:
    """Retrieve the smart (slower but better) model name from environment or fall back to fast model.
    
    Used for complex reasoning tasks like architecture and code generation.
    """
    model_name = os.getenv("SMART_MODEL", get_fast_model_name())
    logger.debug(f"get_smart_model_name() - returning model: {model_name}")
    return model_name

def get_temperature(default: float = 0.2) -> float:
    """Retrieve LLM temperature from environment or use default.
    
    Temperature controls output randomness: 0.0 = deterministic, higher = more creative.
    """
    try:
        temp_str = os.getenv("LLM_TEMPERATURE", str(default))
        temperature = float(temp_str)
        logger.debug(f"get_temperature() - successfully parsed temperature: {temperature}")
        return temperature
    except ValueError as e:
        logger.warning(
            f"get_temperature() - failed to parse LLM_TEMPERATURE='{os.getenv('LLM_TEMPERATURE')}' "
            f"as float, using default: {default}. Error: {e}"
        )
        return default

def create_fast_llm():
    """Create and configure a ChatOpenAI instance for fast model.
    
    This LLM is optimized for speed over output quality.
    """
    fast_model = get_fast_model_name()
    temp = get_temperature()
    logger.info(f"create_fast_llm() - instantiating ChatOpenAI with model={fast_model}, temperature={temp}")
    try:
        llm = ChatOpenAI(
            model=fast_model,
            temperature=temp,
        )
        logger.debug(f"create_fast_llm() - ChatOpenAI instance created successfully")
        return llm
    except Exception as e:
        logger.error(f"create_fast_llm() - failed to create ChatOpenAI instance: {e}", exc_info=True)
        raise

def create_smart_llm():
    """Create and configure a ChatOpenAI instance for smart model.
    
    This LLM prioritizes output quality over speed for complex tasks.
    """
    smart_model = get_smart_model_name()
    temp = get_temperature()
    logger.info(f"create_smart_llm() - instantiating ChatOpenAI with model={smart_model}, temperature={temp}")
    try:
        llm = ChatOpenAI(
            model=smart_model,
            temperature=temp,
        )
        logger.debug(f"create_smart_llm() - ChatOpenAI instance created successfully")
        return llm
    except Exception as e:
        logger.error(f"create_smart_llm() - failed to create ChatOpenAI instance: {e}", exc_info=True)
        raise
