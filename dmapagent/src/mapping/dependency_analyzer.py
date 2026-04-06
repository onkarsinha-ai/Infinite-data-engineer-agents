"""Dependency analyzer for mapping execution order."""
from typing import List, Dict, Set, Optional
from collections import defaultdict, deque
from src.mapping.mapping_lineage import MappingLineage, MappingType, MappingContext
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DependencyAnalyzer:
    """Analyze and resolve mapping dependencies."""

    def __init__(self):
        """Initialize analyzer."""
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)

    def build_dependency_graph(self, lineages: List[MappingLineage]) -> Dict[str, Set[str]]:
        """Build dependency graph from lineages."""
        logger.info(f"Building dependency graph for {len(lineages)} lineages")

        self.graph = defaultdict(set)
        self.reverse_graph = defaultdict(set)

        # For each lineage, check dependencies with other lineages
        for lineage in lineages:
            mapping_id = lineage.mapping_id

            # N:1 aggregation depends on all source fields being available
            if lineage.mapping_type == MappingType.MANY_TO_ONE:
                for source_field in lineage.source_fields:
                    # Find lineages that produce these source fields
                    for other in lineages:
                        if other.mapping_id != mapping_id:
                            if lineage.destination_field in (
                                other.destination_fields if other.destination_fields else []
                            ):
                                self.graph[mapping_id].add(other.mapping_id)
                                self.reverse_graph[other.mapping_id].add(mapping_id)

            # 1:N decomposition feeds into multiple mappings
            elif lineage.mapping_type == MappingType.ONE_TO_MANY:
                for dest_field in lineage.destination_fields:
                    # Find lineages that consume these destination fields
                    for other in lineages:
                        if other.mapping_id != mapping_id:
                            if dest_field in other.source_fields:
                                self.graph[other.mapping_id].add(mapping_id)
                                self.reverse_graph[mapping_id].add(other.mapping_id)

            # Explicit dependencies
            for dep_id in lineage.depends_on:
                self.graph[mapping_id].add(dep_id)
                self.reverse_graph[dep_id].add(mapping_id)

        logger.debug(f"Built dependency graph with {len(self.graph)} nodes")
        return self.graph

    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in graph."""
        logger.info("Detecting circular dependencies")

        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True

            rec_stack.remove(node)
            return False

        for node in self.graph:
            if node not in visited:
                dfs(node, [])

        if cycles:
            logger.warning(f"Found {len(cycles)} circular dependencies")
            for cycle in cycles:
                logger.warning(f"  Cycle: {' -> '.join(cycle)}")

        return cycles

    def resolve_execution_order(self, lineages: List[MappingLineage]) -> List[str]:
        """Resolve execution order using topological sort."""
        logger.info(f"Resolving execution order for {len(lineages)} lineages")

        self.build_dependency_graph(lineages)

        # Check for cycles first
        cycles = self.detect_circular_dependencies()
        if cycles:
            logger.error("Cannot resolve execution order due to circular dependencies")
            return []

        # Topological sort using Kahn's algorithm
        in_degree = {node: 0 for node in [l.mapping_id for l in lineages]}

        for node in self.graph:
            for neighbor in self.graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1

        queue = deque([node for node in in_degree if in_degree[node] == 0])
        execution_order = []

        while queue:
            node = queue.popleft()
            execution_order.append(node)

            for neighbor in self.graph.get(node, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(execution_order) != len(lineages):
            logger.warning(f"Execution order incomplete: {len(execution_order)}/{len(lineages)}")

        logger.info(f"Resolved execution order: {execution_order}")
        return execution_order

    def validate_all_dependencies(self, context: MappingContext) -> bool:
        """Validate all dependencies in context."""
        logger.info("Validating all dependencies")

        # Check for circular dependencies
        if context.circular_dependencies:
            logger.error(f"Found {len(context.circular_dependencies)} circular dependencies")
            return False

        # Check execution order
        if not context.execution_order:
            logger.warning("No execution order defined")
            return False

        # Verify all lineages are in execution order
        execution_ids = set(context.execution_order)
        lineage_ids = set(l.mapping_id for l in context.lineages)

        if execution_ids != lineage_ids:
            missing = lineage_ids - execution_ids
            extra = execution_ids - lineage_ids
            if missing:
                logger.warning(f"Missing from execution order: {missing}")
            if extra:
                logger.warning(f"Extra in execution order: {extra}")

        return len(context.circular_dependencies) == 0

    def get_dependencies_for_lineage(self, lineage_id: str) -> Set[str]:
        """Get all lineages that must execute before this one."""
        return self.graph.get(lineage_id, set())

    def get_dependents_for_lineage(self, lineage_id: str) -> Set[str]:
        """Get all lineages that depend on this one."""
        return self.reverse_graph.get(lineage_id, set())
