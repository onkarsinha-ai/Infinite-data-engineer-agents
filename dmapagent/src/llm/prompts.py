"""LLM prompts for mapping tasks."""
from typing import List, Dict, Any


class MappingPrompts:
    """Prompts for LLM-based mapping tasks."""

    @staticmethod
    def identify_one_to_one_mappings(
        source_fields: List[str], destination_fields: List[str]
    ) -> str:
        """Prompt to identify 1:1 field mappings."""
        return f"""
Analyze the following source and destination fields and identify which source field 
maps to which destination field (one-to-one relationships).

Source Fields:
{chr(10).join(f'- {f}' for f in source_fields)}

Destination Fields:
{chr(10).join(f'- {f}' for f in destination_fields)}

For each destination field, provide:
1. The corresponding source field name
2. Confidence level (HIGH, MEDIUM, LOW)
3. Brief justification

Format your response as JSON:
{{
  "mappings": [
    {{"source": "field_name", "destination": "field_name", "confidence": "HIGH", "reason": "..."}}
  ]
}}
"""

    @staticmethod
    def identify_aggregation_mappings(
        source_fields: List[Dict[str, str]], destination_fields: List[Dict[str, str]]
    ) -> str:
        """Prompt to identify N:1 aggregation mappings."""
        source_str = "\n".join(
            f"- {f['name']} ({f['type']})" for f in source_fields
        )
        dest_str = "\n".join(
            f"- {f['name']} ({f['type']})" for f in destination_fields
        )

        return f"""
Analyze the following source and destination fields and identify which combination of 
source fields should be aggregated into a single destination field (N:1 relationships).

Source Fields:
{source_str}

Destination Fields:
{dest_str}

For each potential aggregation, identify:
1. Which source fields should be combined
2. The destination field they map to
3. The aggregation strategy (CONCAT, SUM, MERGE, etc.)
4. Confidence level

Format your response as JSON:
{{
  "aggregations": [
    {{
      "sources": ["field1", "field2"],
      "destination": "field_name",
      "strategy": "CONCAT",
      "confidence": "HIGH",
      "reason": "..."
    }}
  ]
}}
"""

    @staticmethod
    def identify_decomposition_mappings(
        source_fields: List[Dict[str, str]], destination_fields: List[Dict[str, str]]
    ) -> str:
        """Prompt to identify 1:N decomposition mappings."""
        source_str = "\n".join(
            f"- {f['name']} ({f['type']})" for f in source_fields
        )
        dest_str = "\n".join(
            f"- {f['name']} ({f['type']})" for f in destination_fields
        )

        return f"""
Analyze the following source and destination fields and identify which source field 
should be decomposed into multiple destination fields (1:N relationships).

Source Fields:
{source_str}

Destination Fields:
{dest_str}

For each potential decomposition, identify:
1. Which source field should be split
2. Which destination fields it decomposes to
3. The decomposition strategy (SPLIT, PARSE_JSON, EXTRACT_REGEX, etc.)
4. Confidence level

Format your response as JSON:
{{
  "decompositions": [
    {{
      "source": "field_name",
      "destinations": ["field1", "field2"],
      "strategy": "SPLIT",
      "confidence": "HIGH",
      "reason": "..."
    }}
  ]
}}
"""

    @staticmethod
    def suggest_type_conversion(source_type: str, dest_type: str) -> str:
        """Prompt to suggest type conversion strategy."""
        return f"""
Suggest a safe type conversion strategy from {source_type} to {dest_type}.

Provide:
1. Whether conversion is possible and safe
2. Data loss risks if any
3. Recommended transformation logic
4. Risk level (NONE, LOW, MEDIUM, HIGH, CRITICAL)

Format as JSON:
{{
  "conversion_possible": true,
  "data_loss_risk": "LOW",
  "strategy": "CAST",
  "code_example": "...",
  "warnings": []
}}
"""

    @staticmethod
    def detect_destructive_operations(
        mapping_info: Dict[str, Any]
    ) -> str:
        """Prompt to detect destructive operations."""
        return f"""
Analyze the following data mapping and identify any potentially destructive operations 
(operations that could cause data loss):

Mapping Details:
{mapping_info}

Identify:
1. Whether this mapping is destructive
2. Type of data loss (widening, narrowing, conversion loss, null loss, etc.)
3. Severity (CRITICAL, HIGH, MEDIUM, LOW)
4. Mitigation strategies if any

Format as JSON:
{{
  "is_destructive": false,
  "destruction_type": "NARROWING",
  "severity": "HIGH",
  "affected_data": "...",
  "mitigation": "..."
}}
"""

    @staticmethod
    def generate_aggregation_code(
        sources: List[str], destination: str, strategy: str
    ) -> str:
        """Prompt to generate aggregation code."""
        sources_str = ", ".join(sources)
        return f"""
Generate Python code to aggregate {sources_str} into {destination} using {strategy} strategy.

Requirements:
1. Handle NULL values appropriately
2. Include type conversions if needed
3. Add error handling
4. Include comments

Return only the Python code, no explanation.
"""

    @staticmethod
    def generate_decomposition_code(
        source: str, destinations: List[str], strategy: str
    ) -> str:
        """Prompt to generate decomposition code."""
        dests_str = ", ".join(destinations)
        return f"""
Generate Python code to decompose {source} into {dests_str} using {strategy} strategy.

Requirements:
1. Handle NULL/empty values
2. Validate extraction
3. Handle parse errors
4. Include comments

Return only the Python code, no explanation.
"""

    @staticmethod
    def analyze_schema_relationships(
        source_schema_info: Dict[str, Any], dest_schema_info: Dict[str, Any]
    ) -> str:
        """Prompt to analyze schema relationships."""
        return f"""
Analyze the relationships between the following schemas:

Source Schema:
{source_schema_info}

Destination Schema:
{dest_schema_info}

Identify:
1. Direct field mappings (1:1)
2. Aggregation opportunities (N:1)
3. Decomposition opportunities (1:N)
4. Unmapped fields
5. Data quality issues

Format as JSON with these sections.
"""
