"""dmapagent - Data Mapping Agent for schema transformation and field mapping."""

__version__ = "1.0.0"
__author__ = "Data Mapping Team"

from src.core.schema_extractor import SchemaExtractor
from src.mapping.mapper import DataMapper
from src.graph.workflow import create_mapping_workflow

__all__ = [
    "SchemaExtractor",
    "DataMapper",
    "create_mapping_workflow",
]
