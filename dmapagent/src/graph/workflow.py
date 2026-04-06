"""LangGraph workflow definition."""
from langgraph.graph import StateGraph, START, END
from src.graph.state import WorkflowState
from src.graph.nodes import (
    parse_sources,
    parse_destinations,
    create_mapping_context,
    identify_one_to_one_mappings,
    identify_aggregation_mappings,
    identify_decomposition_mappings,
    detect_destructive_operations,
    resolve_execution_order,
    generate_transformation_code,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_mapping_workflow():
    """Create LangGraph workflow for data mapping."""
    logger.info("Creating mapping workflow")

    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("parse_sources", parse_sources)
    workflow.add_node("parse_destinations", parse_destinations)
    workflow.add_node("create_context", create_mapping_context)
    workflow.add_node("identify_1_to_1", identify_one_to_one_mappings)
    workflow.add_node("identify_n_to_1", identify_aggregation_mappings)
    workflow.add_node("identify_1_to_n", identify_decomposition_mappings)
    workflow.add_node("detect_destructive", detect_destructive_operations)
    workflow.add_node("resolve_order", resolve_execution_order)
    workflow.add_node("generate_code", generate_transformation_code)

    # Add edges
    workflow.add_edge(START, "parse_sources")
    workflow.add_edge(START, "parse_destinations")
    workflow.add_edge("parse_sources", "create_context")
    workflow.add_edge("parse_destinations", "create_context")
    workflow.add_edge("create_context", "identify_1_to_1")
    workflow.add_edge("identify_1_to_1", "identify_n_to_1")
    workflow.add_edge("identify_n_to_1", "identify_1_to_n")
    workflow.add_edge("identify_1_to_n", "detect_destructive")
    workflow.add_edge("detect_destructive", "resolve_order")
    workflow.add_edge("resolve_order", "generate_code")
    workflow.add_edge("generate_code", END)

    return workflow.compile()


def run_mapping_workflow(
    source_files: list,
    destination_files: list,
) -> WorkflowState:
    """Run mapping workflow."""
    logger.info("Starting mapping workflow")

    workflow = create_mapping_workflow()

    initial_state = WorkflowState(
        source_files=source_files,
        destination_files=destination_files,
    )

    final_state = workflow.invoke(initial_state)
    
    logger.info(f"Workflow completed with {len(final_state.errors)} errors and {len(final_state.warnings)} warnings")
    
    return final_state
