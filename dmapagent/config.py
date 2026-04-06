"""Configuration module for dmapagent."""
import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any


class DMAPSettings(BaseSettings):
    """Configuration for Data Mapping Agent."""

    # LLM API Keys
    GOOGLE_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma2"

    # LLM Parameters
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Processing
    DEFAULT_ENCODING: str = "utf-8"
    MAX_DOCUMENT_SIZE_MB: int = 100
    CHUNK_SIZE: int = 1000

    # Data Type Mappings
    DEFAULT_TYPE_MAPPINGS: Dict[str, str] = {
        "int": "INTEGER",
        "integer": "INTEGER",
        "bigint": "BIGINT",
        "decimal": "DECIMAL",
        "numeric": "DECIMAL",
        "float": "FLOAT",
        "double": "DOUBLE",
        "varchar": "VARCHAR",
        "char": "CHAR",
        "text": "TEXT",
        "date": "DATE",
        "datetime": "DATETIME",
        "timestamp": "TIMESTAMP",
        "boolean": "BOOLEAN",
        "bool": "BOOLEAN",
        "json": "JSON",
        "jsonb": "JSONB",
        "uuid": "UUID",
        "blob": "BLOB",
        "clob": "CLOB",
    }

    # Transformation Rules
    AGGREGATION_STRATEGIES: Dict[str, str] = {
        "CONCAT": "Concatenate string fields",
        "MERGE": "Merge objects into JSON",
        "SUM": "Sum numeric values",
        "AVG": "Average numeric values",
        "MAX": "Maximum value",
        "MIN": "Minimum value",
        "FIRST": "First value from list",
        "LAST": "Last value from list",
        "GROUP_ARRAY": "Group into array",
        "MERGE_JSON": "Merge JSON objects",
        "CUSTOM": "Custom aggregation logic",
    }

    DECOMPOSITION_STRATEGIES: Dict[str, str] = {
        "SPLIT": "Split string by delimiter",
        "PARSE_JSON": "Extract fields from JSON",
        "EXTRACT_REGEX": "Extract using regex",
        "DISTRIBUTE": "Distribute value to multiple fields",
        "PARSE_STRUCT": "Parse structured data",
        "CUSTOM": "Custom decomposition logic",
    }

    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings() -> DMAPSettings:
    """Get settings instance."""
    return DMAPSettings()


# Severity Levels for Destructive Operations
SEVERITY_LEVELS = {
    "CRITICAL": 1,  # Data loss guaranteed
    "HIGH": 2,  # High risk of data loss
    "MEDIUM": 3,  # Moderate risk
    "LOW": 4,  # Low risk
    "INFO": 5,  # Informational only
}

# Confidence Thresholds
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.65
CONFIDENCE_LOW = 0.4
