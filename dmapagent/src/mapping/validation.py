"""Validation module for mappings."""
from typing import Dict, List, Any
from src.mapping.mapping_lineage import MappingLineage, MappingContext
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MappingValidator:
    """Validate complete mapping contexts."""

    def validate_context(self, context: MappingContext) -> Dict[str, Any]:
        """Validate entire mapping context."""
        logger.info("Validating mapping context")

        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": context.get_statistics(),
        }

        # Check for unmapped fields
        if context.unmapped_source_fields:
            warning = (
                f"Found {len(context.unmapped_source_fields)} unmapped source fields"
            )
            validation_result["warnings"].append(warning)
            logger.warning(warning)

        if context.unmapped_destination_fields:
            warning = (
                f"Found {len(context.unmapped_destination_fields)} unmapped destination fields"
            )
            validation_result["warnings"].append(warning)
            logger.warning(warning)

        # Check for circular dependencies
        if context.circular_dependencies:
            error = (
                f"Found {len(context.circular_dependencies)} circular dependencies"
            )
            validation_result["errors"].append(error)
            validation_result["valid"] = False
            logger.error(error)

        # Check execution order
        if not context.execution_order:
            error = "No execution order defined"
            validation_result["errors"].append(error)
            validation_result["valid"] = False
            logger.error(error)

        # Validate each lineage
        for lineage in context.lineages:
            self._validate_lineage(lineage, validation_result)

        return validation_result

    def _validate_lineage(self, lineage: MappingLineage, result: Dict[str, Any]) -> None:
        """Validate individual lineage."""
        if not lineage.source_fields and not lineage.destination_fields:
            result["errors"].append(f"Lineage {lineage.mapping_id} has no source or destination")
            result["valid"] = False
