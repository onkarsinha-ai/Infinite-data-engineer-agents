"""LangGraph workflow nodes for mapping process."""
import json
from typing import Dict, Any, List
from src.graph.state import WorkflowState
from src.core.schema_extractor import SchemaExtractor
from src.llm.llm_provider import get_llm_provider
from src.llm.prompts import MappingPrompts
from src.mapping.mapping_lineage import (
    MappingLineage,
    MappingType,
    MappingContext,
    FieldMapping,
)
from src.mapping.aggregation_engine import AggregationEngine
from src.mapping.decomposition_engine import DecompositionEngine
from src.mapping.dependency_analyzer import DependencyAnalyzer
from src.mapping.transformation import TransformationEngine
from src.utils.logger import get_logger

logger = get_logger(__name__)


def parse_sources(state: WorkflowState) -> WorkflowState:
    """Parse source files and extract schemas."""
    logger.info(f"Parsing {len(state.source_files)} source files")

    extractor = SchemaExtractor()
    try:
        schemas = extractor.extract_from_multiple_files(state.source_files)
        state.source_schemas = schemas

        for name, schema in schemas.items():
            normalized = extractor.normalize_schema(schema)
            state.source_schemas[name] = normalized
            stats = extractor.get_schema_statistics(normalized)
            logger.info(f"Parsed source schema {name}: {stats['table_count']} tables, {stats['total_fields']} fields")

    except Exception as e:
        logger.error(f"Error parsing sources: {e}")
        state.errors.append(f"Failed to parse source files: {str(e)}")

    return state


def parse_destinations(state: WorkflowState) -> WorkflowState:
    """Parse destination files and extract schemas."""
    logger.info(f"Parsing {len(state.destination_files)} destination files")

    extractor = SchemaExtractor()
    try:
        schemas = extractor.extract_from_multiple_files(state.destination_files)
        state.destination_schemas = schemas

        for name, schema in schemas.items():
            normalized = extractor.normalize_schema(schema)
            state.destination_schemas[name] = normalized
            stats = extractor.get_schema_statistics(normalized)
            logger.info(f"Parsed destination schema {name}: {stats['table_count']} tables, {stats['total_fields']} fields")

    except Exception as e:
        logger.error(f"Error parsing destinations: {e}")
        state.errors.append(f"Failed to parse destination files: {str(e)}")

    return state


def create_mapping_context(state: WorkflowState) -> WorkflowState:
    """Create and initialize mapping context."""
    logger.info("Creating mapping context")

    state.mapping_context = MappingContext()
    state.mapping_context.source_schemas = state.source_schemas
    state.mapping_context.destination_schemas = state.destination_schemas

    # Collect all source and destination fields
    source_fields = set()
    dest_fields = set()

    for schema in state.source_schemas.values():
        for field in schema.get_all_fields():
            source_fields.add(f"{schema.name}.{field.name}")

    for schema in state.destination_schemas.values():
        for field in schema.get_all_fields():
            dest_fields.add(f"{schema.name}.{field.name}")

    logger.info(f"Collected {len(source_fields)} source fields and {len(dest_fields)} destination fields")

    return state


def identify_one_to_one_mappings(state: WorkflowState) -> WorkflowState:
    """Use LLM to identify 1:1 mappings."""
    logger.info("Identifying 1:1 mappings using LLM")

    try:
        llm_provider = get_llm_provider()
        logger.info(f"Using LLM provider: {llm_provider.get_current_llm_name()}")

        # Extract field names for LLM
        source_field_names = []
        dest_field_names = []

        for schema in state.source_schemas.values():
            for field in schema.get_all_fields():
                source_field_names.append(f"{field.table_name}.{field.name} ({field.type_info.base_type.value})")

        for schema in state.destination_schemas.values():
            for field in schema.get_all_fields():
                dest_field_names.append(f"{field.table_name}.{field.name} ({field.type_info.base_type.value})")

        # Get LLM suggestions
        prompt = MappingPrompts.identify_one_to_one_mappings(source_field_names, dest_field_names)
        response = llm_provider.invoke(prompt)

        # Parse LLM response
        try:
            response_json = json.loads(response)
            logger.debug(f"LLM suggested {len(response_json.get('mappings', []))} 1:1 mappings")
            # TODO: Convert LLM suggestions to MappingLineage objects
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response for 1:1 mappings")
            state.warnings.append("LLM response parsing failed for 1:1 mappings")

    except Exception as e:
        logger.error(f"Error identifying 1:1 mappings: {e}")
        state.errors.append(f"Failed to identify 1:1 mappings: {str(e)}")

    return state


def identify_aggregation_mappings(state: WorkflowState) -> WorkflowState:
    """Identify N:1 aggregation opportunities."""
    logger.info("Identifying N:1 aggregation mappings")

    try:
        llm_provider = get_llm_provider()
        agg_engine = AggregationEngine()

        # Prepare field info for LLM
        source_fields = []
        dest_fields = []

        for schema in state.source_schemas.values():
            for field in schema.get_all_fields():
                source_fields.append({
                    "name": field.name,
                    "type": field.type_info.base_type.value,
                    "table": field.table_name,
                })

        for schema in state.destination_schemas.values():
            for field in schema.get_all_fields():
                dest_fields.append({
                    "name": field.name,
                    "type": field.type_info.base_type.value,
                    "table": field.table_name,
                })

        prompt = MappingPrompts.identify_aggregation_mappings(source_fields, dest_fields)
        response = llm_provider.invoke(prompt)

        try:
            response_json = json.loads(response)
            logger.debug(f"LLM suggested {len(response_json.get('aggregations', []))} aggregations")
            # TODO: Convert LLM suggestions to MappingLineage objects
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response for aggregations")

    except Exception as e:
        logger.error(f"Error identifying aggregations: {e}")
        state.errors.append(f"Failed to identify aggregations: {str(e)}")

    return state


def identify_decomposition_mappings(state: WorkflowState) -> WorkflowState:
    """Identify 1:N decomposition opportunities."""
    logger.info("Identifying 1:N decomposition mappings")

    try:
        llm_provider = get_llm_provider()
        decomp_engine = DecompositionEngine()

        # Prepare field info for LLM
        source_fields = []
        dest_fields = []

        for schema in state.source_schemas.values():
            for field in schema.get_all_fields():
                source_fields.append({
                    "name": field.name,
                    "type": field.type_info.base_type.value,
                    "table": field.table_name,
                })

        for schema in state.destination_schemas.values():
            for field in schema.get_all_fields():
                dest_fields.append({
                    "name": field.name,
                    "type": field.type_info.base_type.value,
                    "table": field.table_name,
                })

        prompt = MappingPrompts.identify_decomposition_mappings(source_fields, dest_fields)
        response = llm_provider.invoke(prompt)

        try:
            response_json = json.loads(response)
            logger.debug(f"LLM suggested {len(response_json.get('decompositions', []))} decompositions")
            # TODO: Convert LLM suggestions to MappingLineage objects
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response for decompositions")

    except Exception as e:
        logger.error(f"Error identifying decompositions: {e}")
        state.errors.append(f"Failed to identify decompositions: {str(e)}")

    return state


def detect_destructive_operations(state: WorkflowState) -> WorkflowState:
    """Detect destructive operations in mappings."""
    logger.info("Detecting destructive operations")

    try:
        all_mappings = state.one_to_one_mappings + state.many_to_one_mappings + state.one_to_many_mappings
        
        for mapping in all_mappings:
            # Check for destructive operations
            # This will be populated by LLM and other engines
            if mapping.is_destructive:
                state.destructive_mappings.append(mapping)

        logger.info(f"Found {len(state.destructive_mappings)} destructive mappings")

    except Exception as e:
        logger.error(f"Error detecting destructive operations: {e}")
        state.errors.append(f"Failed to detect destructive operations: {str(e)}")

    return state


def resolve_execution_order(state: WorkflowState) -> WorkflowState:
    """Resolve mapping execution order using dependency analysis."""
    logger.info("Resolving execution order")

    try:
        analyzer = DependencyAnalyzer()
        all_mappings = state.one_to_one_mappings + state.many_to_one_mappings + state.one_to_many_mappings

        execution_order = analyzer.resolve_execution_order(all_mappings)
        state.execution_order = execution_order
        state.mapping_context.execution_order = execution_order

        # Check for circular dependencies
        cycles = analyzer.detect_circular_dependencies()
        if cycles:
            state.circular_dependencies = [str(c) for c in cycles]
            state.warnings.append(f"Found {len(cycles)} circular dependencies")

        logger.info(f"Execution order resolved: {len(execution_order)} mappings")

    except Exception as e:
        logger.error(f"Error resolving execution order: {e}")
        state.errors.append(f"Failed to resolve execution order: {str(e)}")

    return state


def generate_transformation_code(state: WorkflowState) -> WorkflowState:
    """Generate transformation code for all mappings."""
    logger.info("Generating transformation code")

    try:
        trans_engine = TransformationEngine()
        all_mappings = state.one_to_one_mappings + state.many_to_one_mappings + state.one_to_many_mappings

        for mapping in all_mappings:
            pipeline = trans_engine.build_transformation_pipeline(mapping)
            logger.debug(f"Generated pipeline for {mapping.mapping_id}: {len(pipeline)} steps")

    except Exception as e:
        logger.error(f"Error generating transformation code: {e}")
        state.errors.append(f"Failed to generate transformation code: {str(e)}")

    return state
