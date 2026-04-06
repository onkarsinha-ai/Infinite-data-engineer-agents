"""Core mapping orchestrator."""
from typing import List, Dict, Optional
from src.mapping.mapping_lineage import MappingLineage, MappingContext, MappingType
from src.core.schema_extractor import Schema, Field
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataMapper:
    """Main mapper orchestrating schema transformations."""

    def __init__(self):
        """Initialize mapper."""
        self.context = MappingContext()

    def set_source_schemas(self, schemas: Dict[str, Schema]) -> None:
        """Set source schemas."""
        self.context.source_schemas = schemas
        logger.info(f"Set {len(schemas)} source schemas")

    def set_destination_schemas(self, schemas: Dict[str, Schema]) -> None:
        """Set destination schemas."""
        self.context.destination_schemas = schemas
        logger.info(f"Set {len(schemas)} destination schemas")

    def add_lineage(self, lineage: MappingLineage) -> None:
        """Add mapping lineage."""
        self.context.add_lineage(lineage)
        logger.debug(f"Added lineage: {lineage}")

    def get_context(self) -> MappingContext:
        """Get current mapping context."""
        return self.context

    def reset(self) -> None:
        """Reset mapper state."""
        self.context = MappingContext()
        logger.info("Mapper reset")
