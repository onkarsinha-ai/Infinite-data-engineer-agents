"""Workflow state definition for LangGraph."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.mapping.mapping_lineage import MappingLineage, MappingContext
from src.core.schema_extractor import Schema


@dataclass
class WorkflowState:
    """State for LangGraph mapping workflow."""

    # Input
    source_files: List[str] = field(default_factory=list)
    destination_files: List[str] = field(default_factory=list)
    
    # Parsed schemas
    source_schemas: Dict[str, Schema] = field(default_factory=dict)
    destination_schemas: Dict[str, Schema] = field(default_factory=dict)
    
    # Mapping context
    mapping_context: Optional[MappingContext] = None
    
    # Results
    one_to_one_mappings: List[MappingLineage] = field(default_factory=list)
    many_to_one_mappings: List[MappingLineage] = field(default_factory=list)
    one_to_many_mappings: List[MappingLineage] = field(default_factory=list)
    
    # Analysis
    unmapped_sources: List[str] = field(default_factory=list)
    unmapped_destinations: List[str] = field(default_factory=list)
    circular_dependencies: List[str] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    
    # Destructive operations
    destructive_mappings: List[MappingLineage] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
