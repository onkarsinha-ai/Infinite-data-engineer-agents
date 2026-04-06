"""Decomposition engine for 1:N mappings."""
from typing import List, Optional, Dict, Any
from src.mapping.mapping_lineage import (
    DecompositionRule,
    DecompositionStrategy,
    FieldMapping,
    MappingType,
)
from src.core.schema_extractor import Field
from src.core.data_types import TypeInfo, SQLDataType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DecompositionEngine:
    """Engine for handling decomposition of one source to multiple destinations."""

    def __init__(self):
        """Initialize decomposition engine."""
        self.strategy_templates = self._init_strategy_templates()

    def _init_strategy_templates(self) -> Dict[str, str]:
        """Initialize strategy code templates."""
        return {
            DecompositionStrategy.SPLIT: "result = {field}.split('{delimiter}')",
            DecompositionStrategy.PARSE_JSON: "import json\nresult = json.loads({field})",
            DecompositionStrategy.EXTRACT_REGEX: "import re\nresult = re.match(r'{pattern}', {field}).groups()",
            DecompositionStrategy.DISTRIBUTE: "result = [{field}] * len(destination_fields)",
            DecompositionStrategy.PARSE_STRUCT: "result = parse_struct({field})",
        }

    def analyze_decomposition(
        self,
        source_field: Field,
        destination_fields: List[Field],
    ) -> Optional[DecompositionRule]:
        """Analyze if decomposition is possible and suggest strategy."""
        if not destination_fields:
            logger.warning("No destination fields provided for decomposition analysis")
            return None

        logger.info(
            f"Analyzing decomposition: {source_field.name} -> {[f.name for f in destination_fields]}"
        )

        # Determine best strategy based on types
        strategy = self._determine_strategy(source_field, destination_fields)

        if not strategy:
            logger.warning("Could not determine decomposition strategy")
            return None

        # Generate decomposition expression and code
        expression = self._generate_expression(strategy, source_field, destination_fields)
        code = self._generate_decomposition_code(strategy, source_field, destination_fields)

        # Check for data loss
        is_destructive, data_loss_desc = self._detect_data_loss(
            source_field, destination_fields, strategy
        )

        rule = DecompositionRule(
            strategy=strategy,
            source_field=source_field,
            destination_fields=destination_fields,
            decomposition_expression=expression,
            decomposition_code=code,
            is_destructive=is_destructive,
            data_loss_description=data_loss_desc,
        )

        logger.debug(f"Created decomposition rule: {rule}")
        return rule

    def _determine_strategy(
        self, source_field: Field, destination_fields: List[Field]
    ) -> Optional[DecompositionStrategy]:
        """Determine best decomposition strategy."""
        # If source is JSON -> PARSE_JSON
        if source_field.type_info.base_type in [SQLDataType.JSON, SQLDataType.JSONB]:
            return DecompositionStrategy.PARSE_JSON

        # If source is VARCHAR and dest fields are various -> SPLIT
        if source_field.type_info.base_type in [
            SQLDataType.VARCHAR,
            SQLDataType.TEXT,
            SQLDataType.CHAR,
        ]:
            if len(destination_fields) > 1:
                return DecompositionStrategy.SPLIT

        # If all destination types are same as source -> DISTRIBUTE
        if all(
            f.type_info.base_type == source_field.type_info.base_type
            for f in destination_fields
        ):
            return DecompositionStrategy.DISTRIBUTE

        # Check if it looks like structured data (XML, CSV)
        if ":" in source_field.raw_definition or "|" in source_field.raw_definition:
            return DecompositionStrategy.PARSE_STRUCT

        # Default: SPLIT
        if source_field.type_info.base_type in [
            SQLDataType.VARCHAR,
            SQLDataType.TEXT,
            SQLDataType.CHAR,
        ]:
            return DecompositionStrategy.SPLIT

        return None

    def _generate_expression(
        self,
        strategy: DecompositionStrategy,
        source_field: Field,
        destination_fields: List[Field],
    ) -> str:
        """Generate decomposition expression."""
        dest_names = ", ".join(f'"{f.name}"' for f in destination_fields)

        if strategy == DecompositionStrategy.SPLIT:
            return f"SPLIT({source_field.name}, ',') -> ({dest_names})"
        elif strategy == DecompositionStrategy.PARSE_JSON:
            return f"PARSE_JSON({source_field.name}) -> ({dest_names})"
        elif strategy == DecompositionStrategy.EXTRACT_REGEX:
            return f"EXTRACT_REGEX({source_field.name}, pattern) -> ({dest_names})"
        elif strategy == DecompositionStrategy.DISTRIBUTE:
            return f"DISTRIBUTE({source_field.name}) -> ({dest_names})"
        elif strategy == DecompositionStrategy.PARSE_STRUCT:
            return f"PARSE_STRUCT({source_field.name}) -> ({dest_names})"
        else:
            return f"{strategy.value}({source_field.name}) -> ({dest_names})"

    def _generate_decomposition_code(
        self,
        strategy: DecompositionStrategy,
        source_field: Field,
        destination_fields: List[Field],
    ) -> str:
        """Generate Python code for decomposition."""
        code_lines = []

        if strategy == DecompositionStrategy.SPLIT:
            code_lines.append(f"parts = {source_field.name}.split(',')")
            for idx, dest_field in enumerate(destination_fields):
                code_lines.append(f"{dest_field.name} = parts[{idx}].strip() if {idx} < len(parts) else None")

        elif strategy == DecompositionStrategy.PARSE_JSON:
            code_lines.append(f"import json")
            code_lines.append(f"data = json.loads({source_field.name})")
            for dest_field in destination_fields:
                code_lines.append(
                    f"{dest_field.name} = data.get('{dest_field.name}', None)"
                )

        elif strategy == DecompositionStrategy.EXTRACT_REGEX:
            code_lines.append(f"import re")
            code_lines.append(f"match = re.match(r'pattern', {source_field.name})")
            for idx, dest_field in enumerate(destination_fields):
                code_lines.append(
                    f"{dest_field.name} = match.group({idx + 1}) if match else None"
                )

        elif strategy == DecompositionStrategy.DISTRIBUTE:
            for dest_field in destination_fields:
                code_lines.append(f"{dest_field.name} = {source_field.name}")

        elif strategy == DecompositionStrategy.PARSE_STRUCT:
            code_lines.append(f"# Parse structured data from {source_field.name}")
            for dest_field in destination_fields:
                code_lines.append(f"{dest_field.name} = None  # Extract from structure")

        return "\n".join(code_lines)

    def _detect_data_loss(
        self,
        source_field: Field,
        destination_fields: List[Field],
        strategy: DecompositionStrategy,
    ) -> tuple[bool, str]:
        """Detect potential data loss in decomposition."""
        is_destructive = False
        details = []

        # Decomposition with fewer destination fields than source capacity
        if strategy == DecompositionStrategy.SPLIT:
            details.append(
                f"Splitting {source_field.name} into {len(destination_fields)} fields may lose data"
            )
            is_destructive = True

        # Type mismatches
        for dest_field in destination_fields:
            if dest_field.type_info.base_type != source_field.type_info.base_type:
                details.append(
                    f"Type conversion {source_field.type_info.base_type} -> {dest_field.type_info.base_type}"
                )

        # If source can be NULL but destinations are NOT NULL
        if source_field.nullable:
            non_nullable_dests = [f for f in destination_fields if not f.nullable]
            if non_nullable_dests:
                is_destructive = True
                dest_names = ", ".join(f.name for f in non_nullable_dests)
                details.append(f"Source can be NULL but {dest_names} are NOT NULL")

        # If source is smaller and destination is wider precision
        if source_field.type_info.precision and any(
            f.type_info.precision and f.type_info.precision < source_field.type_info.precision
            for f in destination_fields
        ):
            is_destructive = True
            details.append("Some destination fields have narrower precision than source")

        data_loss_desc = "; ".join(details) if details else "No known data loss"
        return is_destructive, data_loss_desc

    def validate_decomposition(self, rule: DecompositionRule) -> bool:
        """Validate decomposition rule."""
        if not rule.source_field:
            logger.warning("Decomposition rule has no source field")
            return False

        if not rule.destination_fields:
            logger.warning("Decomposition rule has no destination fields")
            return False

        return True
