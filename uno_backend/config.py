from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_sambanova import ChatSambaNovaCloud
from langchain_cerebras import ChatCerebras
from langchain_openai import ChatOpenAI


PROVIDERS_CONFIG = {
    "openai": {
        "class": ChatOpenAI,
        "default_model": "gpt-5",
        "supported_models": ["gpt-5", "gpt-4.1"],
        "api_key_env": "OPENAI_API_KEY",
        "description": "OpenAI models",
    },
    "gemini": {
        "class": ChatGoogleGenerativeAI,
        "default_model": "gemini-2.5-pro",
        "supported_models": ["gemini-2.5-pro", "gemma-3-12b-it", "gemini-2.5-flash"],
        "api_key_env": "GEMINI_API_KEY",
        "description": "Google models",
    },
    "groq": {
        "class": ChatGroq,
        "default_model": "openai/gpt-oss-120b",
        "supported_models": [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "moonshotai/kimi-k2-instruct",
        ],
        "api_key_env": "GROQ_API_KEY",
        "description": "Groq models",
    },
    "cerebras": {
        "class": ChatCerebras,
        "default_model": "qwen-3-235b-a22b-thinking-2507",
        "supported_models": [
            "gpt-oss-120b",
            "qwen-3-235b-a22b-thinking-2507",
            "qwen-3-32b",
            "llama-4-maverick-17b-128e-instruct",
        ],
        "api_key_env": "CEREBRAS_API_KEY",
        "description": "Cerebras models",
    },
    "sambanova": {
        "class": ChatSambaNovaCloud,
        "default_model": "DeepSeek-R1-0528",
        "supported_models": [
            "DeepSeek-R1-0528",
            "Meta-Llama-3.3-70B-Instruct",
            "Llama-4-Maverick-17B-128E-Instruct"
        ],
        "api_key_env": "SAMBANOVA_API_KEY",
        "description": "SambaNova Systems models",
        "extra_args": {"max_tokens": 7168},
    },
}