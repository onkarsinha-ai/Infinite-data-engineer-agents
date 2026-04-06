"""Mapping lineage and multi-source/multi-destination tracking."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from src.utils.helpers import generate_id
from src.core.schema_extractor import Field
from src.core.data_types import TypeInfo


class MappingType(str, Enum):
    """Types of mappings."""

    ONE_TO_ONE = "1:1"  # Single source field to single destination
    MANY_TO_ONE = "N:1"  # Multiple source fields to single destination (aggregation)
    ONE_TO_MANY = "1:N"  # Single source field to multiple destinations (decomposition)
    MANY_TO_MANY = "N:N"  # Complex many-to-many mapping


class AggregationStrategy(str, Enum):
    """Aggregation strategies for N:1 mappings."""

    CONCAT = "CONCAT"
    MERGE = "MERGE"
    SUM = "SUM"
    AVG = "AVG"
    MAX = "MAX"
    MIN = "MIN"
    FIRST = "FIRST"
    LAST = "LAST"
    GROUP_ARRAY = "GROUP_ARRAY"
    MERGE_JSON = "MERGE_JSON"
    CUSTOM = "CUSTOM"


class DecompositionStrategy(str, Enum):
    """Decomposition strategies for 1:N mappings."""

    SPLIT = "SPLIT"
    PARSE_JSON = "PARSE_JSON"
    EXTRACT_REGEX = "EXTRACT_REGEX"
    DISTRIBUTE = "DISTRIBUTE"
    PARSE_STRUCT = "PARSE_STRUCT"
    CUSTOM = "CUSTOM"


@dataclass
class FieldMapping:
    """Individual field mapping."""

    source_field: Optional[Field]  # None for some N:1 cases
    dest_field: Optional[Field]  # None for some 1:N cases
    mapping_type: MappingType
    requires_conversion: bool = False
    is_destructive: bool = False
    destruction_risk: str = "NONE"  # NONE, LOW, MEDIUM, HIGH, CRITICAL
    transformation_rule: str = ""
    transformation_code: str = ""
    confidence: float = 1.0
    notes: str = ""
    field_mapping_id: str = field(default_factory=lambda: generate_id("fmap"))

    def __str__(self) -> str:
        if self.mapping_type == MappingType.ONE_TO_ONE:
            return f"{self.source_field} -> {self.dest_field}"
        return f"({self.mapping_type}) -> {self.dest_field or self.source_field}"


@dataclass
class AggregationRule:
    """Rule for aggregating multiple source fields to one destination."""

    strategy: AggregationStrategy
    source_fields: List[Field]
    destination_field: Field
    aggregation_expression: str  # e.g., "CONCAT({0}, ' ', {1})"
    aggregation_code: str = ""  # Python/SQL code snippet
    is_destructive: bool = False
    data_loss_description: str = ""
    requires_ordering: bool = False
    custom_logic: Optional[str] = None
    rule_id: str = field(default_factory=lambda: generate_id("agg"))

    def __str__(self) -> str:
        fields_str = ", ".join(f.name for f in self.source_fields)
        return f"({fields_str}) -> {self.destination_field.name} via {self.strategy}"


@dataclass
class DecompositionRule:
    """Rule for decomposing a single source field to multiple destinations."""

    strategy: DecompositionStrategy
    source_field: Field
    destination_fields: List[Field]
    decomposition_expression: str  # e.g., "SPLIT({0}, ',')"
    decomposition_code: str = ""  # Python/SQL code snippet
    is_destructive: bool = False
    data_loss_description: str = ""
    delimiter: Optional[str] = None  # For SPLIT strategy
    regex_pattern: Optional[str] = None  # For EXTRACT_REGEX strategy
    custom_logic: Optional[str] = None
    rule_id: str = field(default_factory=lambda: generate_id("decomp"))

    def __str__(self) -> str:
        fields_str = ", ".join(f.name for f in self.destination_fields)
        return f"{self.source_field.name} -> ({fields_str}) via {self.strategy}"


@dataclass
class MappingLineage:
    """Complete mapping lineage from sources to destination."""

    mapping_id: str = field(default_factory=lambda: generate_id("map"))
    mapping_type: MappingType = MappingType.ONE_TO_ONE
    
    # For 1:1 and N:1
    source_fields: List[Field] = field(default_factory=list)
    destination_field: Optional[Field] = None
    
    # For 1:N and N:N
    destination_fields: List[Field] = field(default_factory=list)
    
    # Aggregation info (for N:1)
    aggregation_rule: Optional[AggregationRule] = None
    
    # Decomposition info (for 1:N)
    decomposition_rule: Optional[DecompositionRule] = None
    
    # Transformation pipeline
    transformation_pipeline: List[FieldMapping] = field(default_factory=list)
    
    # Detection
    is_destructive: bool = False
    destruction_type: str = ""  # 'narrowing', 'conversion_risk', 'aggregation_loss', 'decomposition_loss'
    destruction_details: str = ""
    confidence: float = 0.5
    
    # Execution
    execution_order: int = 0
    depends_on: List[str] = field(default_factory=list)  # IDs of other mappings
    
    # Metadata
    notes: str = ""
    source_file: str = ""
    destination_file: str = ""

    def __str__(self) -> str:
        if self.mapping_type == MappingType.ONE_TO_ONE:
            return f"1:1 {self.source_fields[0].name if self.source_fields else '?'} -> {self.destination_field.name if self.destination_field else '?'}"
        elif self.mapping_type == MappingType.MANY_TO_ONE:
            sources = ", ".join(f.name for f in self.source_fields)
            return f"N:1 ({sources}) -> {self.destination_field.name if self.destination_field else '?'}"
        elif self.mapping_type == MappingType.ONE_TO_MANY:
            dests = ", ".join(f.name for f in self.destination_fields)
            return f"1:N {self.source_fields[0].name if self.source_fields else '?'} -> ({dests})"
        else:
            return f"N:N -> Complex Mapping"

    def add_dependency(self, mapping_id: str) -> None:
        """Add execution dependency."""
        if mapping_id not in self.depends_on:
            self.depends_on.append(mapping_id)


@dataclass
class MappingContext:
    """Complete context for all mappings."""

    source_schemas: Dict[str, Any] = field(default_factory=dict)  # schema_name -> Schema
    destination_schemas: Dict[str, Any] = field(default_factory=dict)  # schema_name -> Schema
    lineages: List[MappingLineage] = field(default_factory=list)
    
    unmapped_source_fields: List[Field] = field(default_factory=list)
    unmapped_destination_fields: List[Field] = field(default_factory=list)
    
    circular_dependencies: List[str] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)  # Ordered mapping IDs
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    context_id: str = field(default_factory=lambda: generate_id("ctx"))

    def add_lineage(self, lineage: MappingLineage) -> None:
        """Add mapping lineage."""
        self.lineages.append(lineage)

    def get_lineage_by_id(self, mapping_id: str) -> Optional[MappingLineage]:
        """Get lineage by ID."""
        for lineage in self.lineages:
            if lineage.mapping_id == mapping_id:
                return lineage
        return None

    def get_lineages_by_type(self, mapping_type: MappingType) -> List[MappingLineage]:
        """Get lineages by type."""
        return [l for l in self.lineages if l.mapping_type == mapping_type]

    def get_destructive_lineages(self) -> List[MappingLineage]:
        """Get all destructive mappings."""
        return [l for l in self.lineages if l.is_destructive]

    def get_statistics(self) -> Dict[str, Any]:
        """Get mapping statistics."""
        return {
            "total_mappings": len(self.lineages),
            "one_to_one": len(self.get_lineages_by_type(MappingType.ONE_TO_ONE)),
            "many_to_one": len(self.get_lineages_by_type(MappingType.MANY_TO_ONE)),
            "one_to_many": len(self.get_lineages_by_type(MappingType.ONE_TO_MANY)),
            "destructive_mappings": len(self.get_destructive_lineages()),
            "unmapped_source_fields": len(self.unmapped_source_fields),
            "unmapped_destination_fields": len(self.unmapped_destination_fields),
            "circular_dependencies": len(self.circular_dependencies),
        }
